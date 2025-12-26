# Cloud Telemetry Dialog
"""Dialog for configuring cloud telemetry settings."""

from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import CloudSettings


CLOUD_PROVIDERS = [
    ("AWS IoT Core", "aws_iot"),
    ("Azure IoT Hub", "azure_iot"),
    ("Google Cloud IoT", "google_iot"),
    ("Custom MQTT", "custom"),
]


class CloudSettingsDialog(BaseSettingsDialog):
    """Dialog for cloud telemetry settings."""

    def __init__(self, settings: CloudSettings, parent=None):
        self._settings = settings
        super().__init__("Cloud Telemetry Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Cloud Configuration Group
        cloud_group = self._create_group("Cloud Configuration")
        cloud_layout = QVBoxLayout(cloud_group)
        cloud_layout.setContentsMargins(12, 20, 12, 12)
        cloud_layout.setSpacing(8)

        # Enable cloud
        self._enabled = self._create_checkbox("Enable cloud telemetry", False)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        cloud_layout.addWidget(self._enabled)

        # Provider
        provider_names = [p[0] for p in CLOUD_PROVIDERS]
        self._provider_combo = self._create_combobox(provider_names, "AWS IoT Core")
        cloud_layout.addWidget(SettingsRow("Provider:", self._provider_combo))

        self._content_layout.addWidget(cloud_group)

        # Connection Group
        connection_group = self._create_group("Connection")
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setContentsMargins(12, 20, 12, 12)
        connection_layout.setSpacing(8)

        # Endpoint
        self._endpoint_edit = self._create_lineedit("", "iot.region.amazonaws.com")
        connection_layout.addWidget(SettingsRow(
            "Endpoint:",
            self._endpoint_edit,
            "Cloud provider endpoint URL"
        ))

        # Device ID
        self._device_id_edit = self._create_lineedit("", "racing-dashboard-001")
        connection_layout.addWidget(SettingsRow(
            "Device ID:",
            self._device_id_edit,
            "Unique identifier for this device"
        ))

        self._content_layout.addWidget(connection_group)

        # Upload Group
        upload_group = self._create_group("Data Upload")
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.setContentsMargins(12, 20, 12, 12)
        upload_layout.setSpacing(8)

        # Real-time streaming
        self._realtime = self._create_checkbox("Real-time streaming", True)
        upload_layout.addWidget(SettingsRow(
            "",
            self._realtime,
            "Stream telemetry data in real-time"
        ))

        # Auto upload sessions
        self._auto_upload = self._create_checkbox("Auto-upload sessions", True)
        upload_layout.addWidget(SettingsRow(
            "",
            self._auto_upload,
            "Automatically upload recorded sessions"
        ))

        self._content_layout.addWidget(upload_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle cloud enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._provider_combo.setEnabled(enabled)
        self._endpoint_edit.setEnabled(enabled)
        self._device_id_edit.setEnabled(enabled)
        self._realtime.setEnabled(enabled)
        self._auto_upload.setEnabled(enabled)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)

        for display_name, internal_name in CLOUD_PROVIDERS:
            if internal_name == self._settings.provider:
                self._provider_combo.setCurrentText(display_name)
                break

        self._endpoint_edit.setText(self._settings.endpoint)
        self._device_id_edit.setText(self._settings.device_id)
        self._realtime.setChecked(self._settings.real_time_streaming)
        self._auto_upload.setChecked(self._settings.auto_upload_sessions)

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()

        provider_display = self._provider_combo.currentText()
        for display_name, internal_name in CLOUD_PROVIDERS:
            if display_name == provider_display:
                self._settings.provider = internal_name
                break

        self._settings.endpoint = self._endpoint_edit.text()
        self._settings.device_id = self._device_id_edit.text()
        self._settings.real_time_streaming = self._realtime.isChecked()
        self._settings.auto_upload_sessions = self._auto_upload.isChecked()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(False)
        self._provider_combo.setCurrentText("AWS IoT Core")
        self._endpoint_edit.setText("")
        self._device_id_edit.setText("")
        self._realtime.setChecked(True)
        self._auto_upload.setChecked(True)
