# Dialog Factory
"""Factory for creating configuration dialogs based on tree item selection."""

from typing import Optional, Dict, Callable, Any
from PyQt6.QtWidgets import QDialog, QWidget

from models.dashboard_config import DashboardConfig

from .display_dialog import DisplaySettingsDialog
from .theme_dialog import ThemeSettingsDialog
from .can_dialog import CANSettingsDialog, CANSecurityDialog
from .gps_dialog import GPSSettingsDialog
from .camera_dialog import CameraSettingsDialog
from .cloud_dialog import CloudSettingsDialog
from .voice_dialog import VoiceSettingsDialog
from .logger_dialog import LoggerSettingsDialog
from .laptimer_dialog import LapTimerSettingsDialog
from .ota_dialog import OTASettingsDialog
from .wifi_dialog import WiFiSettingsDialog


# Mapping from tree item text to dialog creation
DIALOG_MAPPING: Dict[str, str] = {
    # Display category
    "Display Settings": "display",
    "Brightness": "display",
    # Theme category
    "Active Theme": "theme",
    "Custom Themes": "theme",
    # CAN category
    "CAN Settings": "can",
    "CAN Security": "can_security",
    # GPS category
    "GPS Settings": "gps",
    "Tracks": "gps",
    # Camera category
    "Camera Settings": "camera",
    "Recording": "camera",
    # Cloud category
    "Cloud Telemetry": "cloud",
    # Voice category
    "Voice Alerts": "voice",
    # Logger category
    "Data Logger": "logger",
    # Lap Timer category
    "Lap Timer Settings": "laptimer",
    # OTA category
    "Update Settings": "ota",
    # WiFi category
    "WiFi Settings": "wifi",
}


class DialogFactory:
    """
    Factory for creating and managing configuration dialogs.
    """

    def __init__(self, config: DashboardConfig, parent: QWidget = None):
        self._config = config
        self._parent = parent
        self._dialogs: Dict[str, QDialog] = {}

    def set_config(self, config: DashboardConfig) -> None:
        """Update the configuration reference."""
        self._config = config
        # Clear cached dialogs when config changes
        self._dialogs.clear()

    def get_dialog_for_item(self, item_text: str) -> Optional[QDialog]:
        """
        Get or create a dialog for the given tree item.
        Returns None if no dialog is available for that item.
        """
        dialog_type = DIALOG_MAPPING.get(item_text)
        if not dialog_type:
            return None

        # Check cache
        if dialog_type in self._dialogs:
            return self._dialogs[dialog_type]

        # Create new dialog
        dialog = self._create_dialog(dialog_type)
        if dialog:
            self._dialogs[dialog_type] = dialog

        return dialog

    def _create_dialog(self, dialog_type: str) -> Optional[QDialog]:
        """Create a dialog of the specified type."""
        if not self._config:
            return None

        dialog_creators = {
            "display": lambda: DisplaySettingsDialog(self._config.display, self._parent),
            "theme": lambda: ThemeSettingsDialog(self._config.theme, self._parent),
            "can": lambda: CANSettingsDialog(self._config.can, self._parent),
            "can_security": lambda: CANSecurityDialog(self._config.can_security, self._parent),
            "gps": lambda: GPSSettingsDialog(self._config.gps, self._parent),
            "camera": lambda: CameraSettingsDialog(self._config.camera, self._parent),
            "cloud": lambda: CloudSettingsDialog(self._config.cloud, self._parent),
            "voice": lambda: VoiceSettingsDialog(self._config.voice, self._parent),
            "logger": lambda: LoggerSettingsDialog(self._config.logger, self._parent),
            "laptimer": lambda: LapTimerSettingsDialog(self._config.lap_timer, self._parent),
            "ota": lambda: OTASettingsDialog(self._config.ota, self._parent),
            "wifi": lambda: WiFiSettingsDialog(self._config.wifi, self._parent),
        }

        creator = dialog_creators.get(dialog_type)
        if creator:
            return creator()

        return None

    def show_dialog_for_item(self, item_text: str) -> bool:
        """
        Show dialog for the given tree item.
        Returns True if a dialog was shown, False otherwise.
        """
        dialog = self.get_dialog_for_item(item_text)
        if dialog:
            # Always create fresh dialog to ensure settings are current
            dialog_type = DIALOG_MAPPING.get(item_text)
            if dialog_type:
                dialog = self._create_dialog(dialog_type)
                if dialog:
                    dialog.exec()
                    return True
        return False

    def clear_cache(self) -> None:
        """Clear the dialog cache."""
        self._dialogs.clear()


def get_dialog_types() -> list:
    """Get list of all available dialog types."""
    return list(set(DIALOG_MAPPING.values()))


def has_dialog(item_text: str) -> bool:
    """Check if an item has an associated dialog."""
    return item_text in DIALOG_MAPPING
