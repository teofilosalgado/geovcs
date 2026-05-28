import posixpath

from osgeo import ogr
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsConnectionsRootItem,
    QgsDataCollectionItem,
    QgsDataItem,
    QgsDataItemProvider,
    QgsLayerItem,
    QgsMessageLog,
)
from qgis.gui import QgsDataItemGuiProvider
from qgis.PyQt.QtWidgets import QAction, QDialog
from qgis.utils import iface

from geovcs.src.dialog import GeoVCSCreateConnectionDialog
from geovcs.src.model import GeoVCSConnection, GeoVCSSettings
from geovcs.src.util import get_icon

PROVIDER_KEY = "GeoVCS"


class GeoVCSLayerItem(QgsLayerItem):
    def __init__(self, parent, name, path, uri, layerType, providerKey):
        super().__init__(parent, name, path, uri, layerType, providerKey)
        self.setCapabilitiesV2(Qgis.BrowserItemCapability.NoCapabilities)
        self.setState(Qgis.BrowserItemState.Populated)

    def hasChildren(self):
        return False


class GeoVCSDataCollectionItem(QgsDataCollectionItem):
    def __init__(self, parent: QgsDataItem, connection: GeoVCSConnection):
        self.connection = connection
        super().__init__(
            parent,
            self.connection.name,
            posixpath.join(parent.path(), self.connection.name),
            PROVIDER_KEY,
        )

    def icon(self):
        return QgsApplication.getThemeIcon("/mIconConnect.svg")

    def hasChildren(self):
        return True

    def _ogr_geometry_type_to_qgis_browser_layer_type(
        self,
        ogr_geometry_type,
    ) -> Qgis.BrowserLayerType:
        if ogr_geometry_type in (
            ogr.wkbPoint,
            ogr.wkbPoint25D,
            ogr.wkbMultiPoint,
            ogr.wkbMultiPoint25D,
        ):
            return Qgis.BrowserLayerType.Point
        elif ogr_geometry_type in (
            ogr.wkbLineString,
            ogr.wkbLineString25D,
            ogr.wkbMultiLineString,
            ogr.wkbMultiLineString25D,
        ):
            return Qgis.BrowserLayerType.Line
        elif ogr_geometry_type in (
            ogr.wkbPolygon,
            ogr.wkbPolygon25D,
            ogr.wkbMultiPolygon,
            ogr.wkbMultiPolygon25D,
        ):
            return Qgis.BrowserLayerType.Polygon
        elif ogr_geometry_type == ogr.wkbNone:
            return Qgis.BrowserLayerType.Table
        else:
            return Qgis.BrowserLayerType.NoType

    def createChildren(self):
        items: GeoVCSLayerItem = []

        datasource = ogr.Open(self.connection.connection_string)
        QgsMessageLog.logMessage(
            f"Connected to GeoVCS {self.connection.name} using '{self.connection.connection_string}'",
            "GeoVCS",
            Qgis.Info,
        )
        layer_count = datasource.GetLayerCount()
        QgsMessageLog.logMessage(
            f"Found {layer_count} layers in {self.connection.name}",
            "GeoVCS",
            Qgis.Info,
        )

        for i in range(layer_count):
            layer = datasource.GetLayer(i)
            item = GeoVCSLayerItem(
                self,
                layer.GetName(),
                posixpath.join(self.path(), layer.GetName()),
                None,
                self._ogr_geometry_type_to_qgis_browser_layer_type(layer.GetGeomType()),
                posixpath.join(
                    f"/{PROVIDER_KEY}", self.connection.name, layer.GetName()
                ),
            )
            items.append(item)
            QgsMessageLog.logMessage(
                f"Layer '{layer.GetName()}' '{layer.GetGeomType()}' loaded from '{self.connection.name}'",
                "GeoVCS",
                Qgis.Info,
            )
        datasource = None

        return items


class GeoVCSConnectionsRootItem(QgsConnectionsRootItem):
    def __init__(self, parent):
        super().__init__(parent, PROVIDER_KEY, f"/{PROVIDER_KEY}", PROVIDER_KEY)

    def icon(self):
        return get_icon("logo.svg")

    def hasChildren(self):
        return True

    def createChildren(self):
        items: list[GeoVCSDataCollectionItem] = []
        for key in GeoVCSSettings.iterate("connections"):
            connection = GeoVCSSettings.read_object(
                posixpath.join("connections", key), GeoVCSConnection
            )
            item = GeoVCSDataCollectionItem(self, connection)
            items.append(item)
        return items


class GeoVCSDataItemProvider(QgsDataItemProvider):
    def name(self):
        return "GeoVCS"

    def capabilities(self):
        return Qgis.DataItemProviderCapability.Databases

    def createDataItem(self, path, parentItem):
        if not parentItem:
            return GeoVCSConnectionsRootItem(parentItem)
        return None


class GeoVCSDataItemGuiProvider(QgsDataItemGuiProvider):
    def name(self):
        return "GeoVCS"

    def populateContextMenu(self, item, menu, selectedItems, context):
        if isinstance(item, GeoVCSConnectionsRootItem):
            action_refresh_connection = QAction(
                QgsApplication.getThemeIcon("/mActionAdd.svg"),
                "New connection...",
                menu,
            )
            action_refresh_connection.triggered.connect(
                lambda: self._create_connection(item)
            )
            menu.addAction(action_refresh_connection)

        if isinstance(item, GeoVCSDataCollectionItem):
            action_refresh_connection = QAction(
                QgsApplication.getThemeIcon("/mActionRefresh.svg"),
                "Refresh",
                menu,
            )
            action_refresh_connection.triggered.connect(
                lambda: self._refresh_connection(item)
            )
            menu.addAction(action_refresh_connection)

    def _refresh_connection(self, item: GeoVCSDataCollectionItem):
        item.refresh()

    def _create_connection(self, item: QgsConnectionsRootItem):
        create_connection_dialog = GeoVCSCreateConnectionDialog()
        if create_connection_dialog.exec() != QDialog.Accepted:
            return

        iface.messageBar().pushMessage(
            "GeoVCS - Connection Created",
            f"Database connection '{create_connection_dialog.get_data().name}' stored successfully.",
            Qgis.MessageLevel.Success,
        )
        item.refresh()
