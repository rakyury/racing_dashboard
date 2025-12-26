# Dialogs package
"""Configuration dialogs for Racing Dashboard."""

from .base_dialog import BaseSettingsDialog, SettingsRow
from .dialog_factory import DialogFactory, has_dialog, get_dialog_types

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
from .template_dialog import TemplateSelectionDialog, show_template_dialog
from .can_editor_dialog import CANEditorDialog, show_can_editor

__all__ = [
    "BaseSettingsDialog",
    "SettingsRow",
    "DialogFactory",
    "has_dialog",
    "get_dialog_types",
    "DisplaySettingsDialog",
    "ThemeSettingsDialog",
    "CANSettingsDialog",
    "CANSecurityDialog",
    "GPSSettingsDialog",
    "CameraSettingsDialog",
    "CloudSettingsDialog",
    "VoiceSettingsDialog",
    "LoggerSettingsDialog",
    "LapTimerSettingsDialog",
    "OTASettingsDialog",
    "WiFiSettingsDialog",
    "TemplateSelectionDialog",
    "show_template_dialog",
    "CANEditorDialog",
    "show_can_editor",
]
