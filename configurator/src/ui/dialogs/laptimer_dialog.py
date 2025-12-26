# Lap Timer Dialog
"""Dialog for configuring lap timer settings."""

from PyQt6.QtWidgets import QVBoxLayout

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import LapTimerSettings


class LapTimerSettingsDialog(BaseSettingsDialog):
    """Dialog for lap timer settings."""

    def __init__(self, settings: LapTimerSettings, parent=None):
        self._settings = settings
        super().__init__("Lap Timer Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Lap Timer Configuration Group
        timer_group = self._create_group("Lap Timer Configuration")
        timer_layout = QVBoxLayout(timer_group)
        timer_layout.setContentsMargins(12, 20, 12, 12)
        timer_layout.setSpacing(8)

        # Enable lap timer
        self._enabled = self._create_checkbox("Enable lap timer", True)
        timer_layout.addWidget(self._enabled)

        # Auto detection
        self._auto_detection = self._create_checkbox("Auto-detect start/finish line", True)
        timer_layout.addWidget(SettingsRow(
            "",
            self._auto_detection,
            "Automatically detect track boundaries from GPS"
        ))

        self._content_layout.addWidget(timer_group)

        # Track Selection Group
        track_group = self._create_group("Track Selection")
        track_layout = QVBoxLayout(track_group)
        track_layout.setContentsMargins(12, 20, 12, 12)
        track_layout.setSpacing(8)

        # Current track
        self._track_edit = self._create_lineedit("", "Enter track name or leave blank for auto")
        track_layout.addWidget(SettingsRow(
            "Current Track:",
            self._track_edit,
            "Leave empty for automatic track detection"
        ))

        self._content_layout.addWidget(track_group)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)
        self._auto_detection.setChecked(self._settings.auto_detection)
        self._track_edit.setText(self._settings.current_track)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()
        self._settings.auto_detection = self._auto_detection.isChecked()
        self._settings.current_track = self._track_edit.text()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._auto_detection.setChecked(True)
        self._track_edit.setText("")
