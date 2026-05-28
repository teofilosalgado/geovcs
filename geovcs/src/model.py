import posixpath
from dataclasses import dataclass
from typing import Any, Generator

from qgis.core import Qgis, QgsMessageLog, QgsSettings

BASE_KEY = "plugins/geovcs"


@dataclass
class GeoVCSConnection:
    name: str
    host: str
    port: int
    database: str
    username: str
    password: str

    @property
    def connection_string(self) -> str:
        value = (
            f"MySQL:{self.database},"
            f"host={self.host},"
            f"port={self.port},"
            f"user={self.username},"
            f"password={self.password}"
        )
        return value


class GeoVCSSettings:
    @staticmethod
    def write_object(key: str, obj):
        settings = QgsSettings()

        for attr_name, attr_value in vars(obj).items():
            if attr_name.startswith("__") or callable(attr_value):
                continue
            final_key = posixpath.join(BASE_KEY, key, attr_name)
            QgsMessageLog.logMessage(
                f"Wrote '{attr_value}' to '{final_key}'", "GeoVCS", Qgis.Success
            )
            settings.setValue(final_key, attr_value)

    @staticmethod
    def read_object[T](base_key: str, obj_type: type[T]) -> T:
        settings = QgsSettings()
        settings.beginGroup(posixpath.join(BASE_KEY, base_key))

        obj: dict[str, Any] = {}
        for key in settings.childKeys():
            value = settings.value(key)
            obj[key] = value
            QgsMessageLog.logMessage(
                f"Read '{value}' from '{posixpath.join(BASE_KEY, base_key, key)}'",
                "GeoVCS",
                Qgis.Success,
            )
        settings.endGroup()

        return obj_type(**obj)

    @staticmethod
    def iterate(key: str) -> Generator[str, Any, None]:
        base_key = posixpath.join(BASE_KEY, key)

        settings = QgsSettings()
        settings.beginGroup(base_key)
        groups = settings.childGroups()

        for group in groups:
            QgsMessageLog.logMessage(
                f"Read: '{group}' from '{key}'", "GeoVCS", Qgis.Success
            )
            yield group
        settings.endGroup()
