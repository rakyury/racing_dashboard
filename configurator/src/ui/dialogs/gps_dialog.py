# GPS Settings Dialog
"""Dialog for configuring GPS settings."""

from PyQt6.QtWidgets import QVBoxLayout

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import GPSSettings


GPS_UPDATE_RATES = ["1", "5", "10", "25", "50"]


class GPSSettingsDialog(BaseSettingsDialog):
    """Dialog for GPS settings."""

    def __init__(self, settings: GPSSettings, parent=None):
        self._settings = settings
        super().__init__("GPS Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # GPS Configuration Group
        gps_group = self._create_group("GPS Configuration")
        gps_layout = QVBoxLayout(gps_group)
        gps_layout.setContentsMargins(12, 20, 12, 12)
        gps_layout.setSpacing(8)

        # Enable GPS
        self._enabled = self._create_checkbox("Enable GPS receiver", True)
        gps_layout.addWidget(self._enabled)

        # Update rate
        self._update_rate_combo = self._create_combobox(GPS_UPDATE_RATES, "25")
        gps_layout.addWidget(SettingsRow(
            "Update Rate:",
            self._update_rate_combo,
            "GPS position updates per second (Hz)"
        ))

        self._content_layout.addWidget(gps_group)

        # Track Detection Group
        track_group = self._create_group("Track Detection")
        track_layout = QVBoxLayout(track_group)
        track_layout.setContentsMargins(12, 20, 12, 12)
        track_layout.setSpacing(8)

        # Auto track detection
        self._auto_track = self._create_checkbox("Auto-detect track", True)
        track_layout.addWidget(SettingsRow(
            "",
            self._auto_track,
            "Automatically identify track from GPS coordinates"
        ))

        self._content_layout.addWidget(track_group)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)
        self._update_rate_combo.setCurrentText(str(self._settings.update_rate))
        self._auto_track.setChecked(self._settings.auto_track_detection)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()
        self._settings.update_rate = int(self._update_rate_combo.currentText())
        self._settings.auto_track_detection = self._auto_track.isChecked()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._update_rate_combo.setCurrentText("25")
        self._auto_track.setChecked(True)
