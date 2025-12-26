# WiFi Settings Dialog
"""Dialog for configuring WiFi settings."""

from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import WiFiSettings


WIFI_CHANNELS = [str(i) for i in range(1, 14)]


class WiFiSettingsDialog(BaseSettingsDialog):
    """Dialog for WiFi settings."""

    def __init__(self, settings: WiFiSettings, parent=None):
        self._settings = settings
        super().__init__("WiFi Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Access Point Group
        ap_group = self._create_group("Access Point Mode")
        ap_layout = QVBoxLayout(ap_group)
        ap_layout.setContentsMargins(12, 20, 12, 12)
        ap_layout.setSpacing(8)

        # Enable AP
        self._ap_enabled = self._create_checkbox("Enable WiFi access point", True)
        self._ap_enabled.stateChanged.connect(self._on_ap_enabled_changed)
        ap_layout.addWidget(self._ap_enabled)

        # SSID
        self._ssid_edit = self._create_lineedit("RacingDashboard", "Network name")
        ap_layout.addWidget(SettingsRow(
            "Network Name:",
            self._ssid_edit,
            "WiFi network SSID"
        ))

        # Password
        self._password_edit = self._create_lineedit("", "Leave empty for open network")
        ap_layout.addWidget(SettingsRow(
            "Password:",
            self._password_edit,
            "WPA2 password (8+ characters, or empty for open)"
        ))

        # Channel
        self._channel_combo = self._create_combobox(WIFI_CHANNELS, "6")
        ap_layout.addWidget(SettingsRow(
            "Channel:",
            self._channel_combo,
            "WiFi channel (1-13)"
        ))

        self._content_layout.addWidget(ap_group)

        # Info Group
        info_group = self._create_group("Connection Info")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(12, 20, 12, 12)
        info_layout.setSpacing(8)

        # Info text
        info_text = self._create_label(
            "When access point is enabled, you can connect to the dashboard\n"
            "from your phone or computer to view live telemetry and\n"
            "configure settings via the web interface.\n\n"
            "Default IP: 192.168.4.1"
        )
        info_text.setStyleSheet("color: #888; font-size: 11px; padding: 8px;")
        info_layout.addWidget(info_text)

        self._content_layout.addWidget(info_group)

    def _on_ap_enabled_changed(self, state: int) -> None:
        """Handle AP enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._ssid_edit.setEnabled(enabled)
        self._password_edit.setEnabled(enabled)
        self._channel_combo.setEnabled(enabled)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._ap_enabled.setChecked(self._settings.ap_enabled)
        self._ssid_edit.setText(self._settings.ap_ssid)
        self._password_edit.setText(self._settings.ap_password)
        self._channel_combo.setCurrentText(str(self._settings.ap_channel))

        self._on_ap_enabled_changed(Qt.CheckState.Checked.value if self._settings.ap_enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.ap_enabled = self._ap_enabled.isChecked()
        self._settings.ap_ssid = self._ssid_edit.text()
        self._settings.ap_password = self._password_edit.text()
        self._settings.ap_channel = int(self._channel_combo.currentText())

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._ap_enabled.setChecked(True)
        self._ssid_edit.setText("RacingDashboard")
        self._password_edit.setText("")
        self._channel_combo.setCurrentText("6")
