# Camera Settings Dialog
"""Dialog for configuring camera integration."""

from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import CameraSettings


CAMERA_TYPES = [
    ("GoPro WiFi", "gopro_wifi"),
    ("Insta360 WiFi", "insta360_wifi"),
    ("RTSP Stream", "rtsp"),
    ("AIM SmartyCam", "aim_smartycam"),
]

TRIGGER_MODES = [
    ("Manual", "manual"),
    ("Ignition On", "ignition"),
    ("Speed Threshold", "speed"),
    ("Lap Start", "lap_start"),
]


class CameraSettingsDialog(BaseSettingsDialog):
    """Dialog for camera integration settings."""

    def __init__(self, settings: CameraSettings, parent=None):
        self._settings = settings
        super().__init__("Camera Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Camera Configuration Group
        camera_group = self._create_group("Camera Configuration")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setContentsMargins(12, 20, 12, 12)
        camera_layout.setSpacing(8)

        # Enable camera
        self._enabled = self._create_checkbox("Enable camera integration", False)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        camera_layout.addWidget(self._enabled)

        # Camera type
        type_names = [t[0] for t in CAMERA_TYPES]
        self._type_combo = self._create_combobox(type_names, "GoPro WiFi")
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        camera_layout.addWidget(SettingsRow("Camera Type:", self._type_combo))

        # IP Address
        self._ip_edit = self._create_lineedit("", "e.g., 10.5.5.9")
        camera_layout.addWidget(SettingsRow(
            "IP Address:",
            self._ip_edit,
            "Camera IP address for WiFi connection"
        ))

        self._content_layout.addWidget(camera_group)

        # Recording Group
        recording_group = self._create_group("Recording")
        recording_layout = QVBoxLayout(recording_group)
        recording_layout.setContentsMargins(12, 20, 12, 12)
        recording_layout.setSpacing(8)

        # Auto record
        self._auto_record = self._create_checkbox("Auto-start recording", True)
        recording_layout.addWidget(self._auto_record)

        # Trigger mode
        trigger_names = [t[0] for t in TRIGGER_MODES]
        self._trigger_combo = self._create_combobox(trigger_names, "Ignition On")
        recording_layout.addWidget(SettingsRow(
            "Trigger Mode:",
            self._trigger_combo,
            "When to start/stop recording"
        ))

        self._content_layout.addWidget(recording_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle camera enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._type_combo.setEnabled(enabled)
        self._ip_edit.setEnabled(enabled)
        self._auto_record.setEnabled(enabled)
        self._trigger_combo.setEnabled(enabled)

    def _on_type_changed(self, camera_type: str) -> None:
        """Handle camera type change."""
        # Show/hide IP field based on type
        needs_ip = camera_type in ["RTSP Stream"]
        # IP always shown but may be optional

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)

        # Find camera type display name
        for display_name, internal_name in CAMERA_TYPES:
            if internal_name == self._settings.camera_type:
                self._type_combo.setCurrentText(display_name)
                break

        self._ip_edit.setText(self._settings.ip_address)
        self._auto_record.setChecked(self._settings.auto_record)

        # Find trigger mode display name
        for display_name, internal_name in TRIGGER_MODES:
            if internal_name == self._settings.trigger_mode:
                self._trigger_combo.setCurrentText(display_name)
                break

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()

        type_display = self._type_combo.currentText()
        for display_name, internal_name in CAMERA_TYPES:
            if display_name == type_display:
                self._settings.camera_type = internal_name
                break

        self._settings.ip_address = self._ip_edit.text()
        self._settings.auto_record = self._auto_record.isChecked()

        trigger_display = self._trigger_combo.currentText()
        for display_name, internal_name in TRIGGER_MODES:
            if display_name == trigger_display:
                self._settings.trigger_mode = internal_name
                break

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(False)
        self._type_combo.setCurrentText("GoPro WiFi")
        self._ip_edit.setText("")
        self._auto_record.setChecked(True)
        self._trigger_combo.setCurrentText("Ignition On")
