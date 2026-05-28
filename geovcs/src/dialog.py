import posixpath

from osgeo import ogr
from qgis.PyQt.QtGui import QIntValidator
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from geovcs.src.model import GeoVCSConnection, GeoVCSSettings


class GeoVCSCreateConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoVCS - New Connection")
        self.resize(450, 200)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Host/Port
        self.txt_host = QLineEdit(self)
        self.txt_host.setPlaceholderText("localhost")

        self.txt_port = QLineEdit(self)
        self.txt_port.setPlaceholderText("3306")
        self.txt_port.setFixedWidth(60)
        self.txt_port.setValidator(QIntValidator(1, 65535, self))

        self.lbl_host_port = QLabel(":")

        self.layout_host_port = QHBoxLayout()
        self.layout_host_port.addWidget(self.txt_host)
        self.layout_host_port.addWidget(self.lbl_host_port)
        self.layout_host_port.addWidget(self.txt_port)
        form_layout.addRow("Host:", self.layout_host_port)

        # Database
        self.txt_database = QLineEdit(self)
        self.txt_database.setPlaceholderText("gis")
        form_layout.addRow("Database:", self.txt_database)

        # Username
        self.txt_username = QLineEdit(self)
        form_layout.addRow("Username:", self.txt_username)

        # Password
        self.txt_password = QLineEdit(self)
        self.txt_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.txt_password)

        # Name
        self.txt_name = QLineEdit(self)
        self.txt_name.setPlaceholderText("localhost@gis@user")
        form_layout.addRow("Name:", self.txt_name)

        layout.addLayout(form_layout)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(
                self, "GeoVCS - Validation Error", "Connection name is required."
            )
            self.txt_name.setFocus()
            return

        if not self.txt_host.text().strip():
            QMessageBox.warning(
                self, "GeoVCS - Validation Error", "Host address is required."
            )
            self.txt_host.setFocus()
            return

        if not self.txt_port.text().strip():
            QMessageBox.warning(
                self, "GeoVCS - Validation Error", "Port number is required."
            )
            self.txt_port.setFocus()
            return

        if not self.txt_database.text().strip():
            QMessageBox.warning(
                self, "GeoVCS - Validation Error", "Database name is required."
            )
            self.txt_database.setFocus()
            return

        if not self.txt_username.text().strip():
            QMessageBox.warning(
                self, "GeoVCS - Validation Error", "Username is required."
            )
            self.txt_username.setFocus()
            return

        if not self.txt_password.text():
            QMessageBox.warning(self, "Validation Error", "Password is required.")
            self.txt_password.setFocus()
            return

        data = self.get_data()
        try:
            datasource = ogr.Open(data.connection_string)
            if datasource is None:
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    "Check your credentials and server availability.",
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Check your credentials and server availability: {e}.",
            )
            return

        datasource = None

        GeoVCSSettings.write_object(posixpath.join("connections", data.name), data)
        return super().accept()

    def get_data(self) -> GeoVCSConnection:
        return GeoVCSConnection(
            name=self.txt_name.text().strip(),
            host=self.txt_host.text().strip(),
            port=int(self.txt_port.text().strip()),
            database=self.txt_database.text().strip(),
            username=self.txt_username.text().strip(),
            password=self.txt_password.text(),
        )
