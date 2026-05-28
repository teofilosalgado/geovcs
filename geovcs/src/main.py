"""
QGIS GeoVCS - Main Plugin Class

This module contains the main plugin class that manages the QGIS interface
integration, menu items, toolbar buttons, and dockable panels.
"""

from qgis.core import QgsApplication
from qgis.gui import QgisInterface, QgsGui

from geovcs.src.browser import GeoVCSDataItemGuiProvider, GeoVCSDataItemProvider


class GeoVCS:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.data_item_provider: GeoVCSDataItemProvider = None
        self.data_item_gui_provider: GeoVCSDataItemGuiProvider = None

    def initGui(self):
        self.data_item_provider = GeoVCSDataItemProvider()
        QgsApplication.dataItemProviderRegistry().addProvider(self.data_item_provider)

        self.data_item_gui_provider = GeoVCSDataItemGuiProvider()
        QgsGui.dataItemGuiProviderRegistry().addProvider(self.data_item_gui_provider)

    def unload(self):
        if self.data_item_provider:
            QgsApplication.dataItemProviderRegistry().removeProvider(
                self.data_item_provider
            )
            self.data_item_provider = None

        if self.data_item_gui_provider:
            QgsGui.dataItemGuiProviderRegistry().removeProvider(
                self.data_item_gui_provider
            )
            self.data_item_gui_provider = None
