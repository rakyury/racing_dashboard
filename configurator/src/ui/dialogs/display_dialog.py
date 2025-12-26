# Display Settings Dialog
"""Dialog for configuring display settings."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import DisplaySettings


# Display profiles with resolutions
DISPLAY_PROFILES = {
    "1024x600": (1024, 600),
    "1280x480": (1280, 480),
    "800x480": (800, 480),
    "480x320": (480, 320),
    "1920x480": (1920, 480),
    "Custom": None,
}

ORIENTATIONS = [
    "Landscape",
    "Portrait",
    "Landscape (Inverted)",
    "Portrait (Inverted)",
]

ORIENTATION_MAP = {
    "Landscape": "landscape",
    "Portrait": "portrait",
    "Landscape (Inverted)": "landscape_inv",
    "Portrait (Inverted)": "portrait_inv",
}


class DisplaySettingsDialog(BaseSettingsDialog):
    """Dialog for display hardware settings."""

    def __init__(self, settings: DisplaySettings, parent=None):
        self._settings = settings
        super().__init__("Display Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Display Profile Group
        profile_group = self._create_group("Display Profile")
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.setContentsMargins(12, 20, 12, 12)
        profile_layout.setSpacing(8)

        # Profile selector
        self._profile_combo = self._create_combobox(list(DISPLAY_PROFILES.keys()))
        self._profile_combo.currentTextChanged.connect(self._on_profile_changed)
        profile_layout.addWidget(SettingsRow(
            "Profile:",
            self._profile_combo,
            "Select display resolution profile"
        ))

        # Resolution display
        res_widget = QWidget()
        res_layout = QHBoxLayout(res_widget)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(8)

        self._width_spin = self._create_spinbox(320, 2048, 1024, "px")
        self._width_spin.setEnabled(False)
        res_layout.addWidget(self._width_spin)

        res_layout.addWidget(QLabel("x"))

        self._height_spin = self._create_spinbox(200, 1200, 600, "px")
        self._height_spin.setEnabled(False)
        res_layout.addWidget(self._height_spin)

        res_layout.addStretch()
        profile_layout.addWidget(SettingsRow("Resolution:", res_widget))

        # Orientation
        self._orientation_combo = self._create_combobox(ORIENTATIONS)
        profile_layout.addWidget(SettingsRow(
            "Orientation:",
            self._orientation_combo,
            "Screen rotation"
        ))

        # Refresh rate
        self._refresh_spin = self._create_spinbox(30, 120, 60, "Hz")
        profile_layout.addWidget(SettingsRow(
            "Refresh Rate:",
            self._refresh_spin,
            "Display refresh rate"
        ))

        self._content_layout.addWidget(profile_group)

        # Brightness Group
        brightness_group = self._create_group("Brightness")
        brightness_layout = QVBoxLayout(brightness_group)
        brightness_layout.setContentsMargins(12, 20, 12, 12)
        brightness_layout.setSpacing(8)

        # Auto brightness
        self._auto_brightness = self._create_checkbox("Auto brightness", True)
        brightness_layout.addWidget(self._auto_brightness)

        # Brightness slider with value label
        brightness_widget = QWidget()
        brightness_inner = QHBoxLayout(brightness_widget)
        brightness_inner.setContentsMargins(0, 0, 0, 0)
        brightness_inner.setSpacing(12)

        self._brightness_slider = self._create_slider(100, 1000, 700)
        self._brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_inner.addWidget(self._brightness_slider)

        self._brightness_label = QLabel("700")
        self._brightness_label.setStyleSheet("color: #fff; min-width: 40px;")
        brightness_inner.addWidget(self._brightness_label)

        brightness_layout.addWidget(SettingsRow(
            "Max Brightness:",
            brightness_widget,
            "Maximum brightness level (cd/m2)"
        ))

        self._content_layout.addWidget(brightness_group)

    def _on_profile_changed(self, profile: str) -> None:
        """Handle profile selection change."""
        if profile in DISPLAY_PROFILES and DISPLAY_PROFILES[profile]:
            width, height = DISPLAY_PROFILES[profile]
            self._width_spin.setValue(width)
            self._height_spin.setValue(height)
            self._width_spin.setEnabled(False)
            self._height_spin.setEnabled(False)
        elif profile == "Custom":
            self._width_spin.setEnabled(True)
            self._height_spin.setEnabled(True)

    def _on_brightness_changed(self, value: int) -> None:
        """Update brightness label."""
        self._brightness_label.setText(str(value))

    def _load_settings(self) -> None:
        """Load settings into UI."""
        # Find matching profile
        resolution = (self._settings.width, self._settings.height)
        profile_found = False
        for profile, res in DISPLAY_PROFILES.items():
            if res == resolution:
                self._profile_combo.setCurrentText(profile)
                profile_found = True
                break

        if not profile_found:
            self._profile_combo.setCurrentText("Custom")
            self._width_spin.setEnabled(True)
            self._height_spin.setEnabled(True)

        self._width_spin.setValue(self._settings.width)
        self._height_spin.setValue(self._settings.height)

        # Find orientation
        for display_name, internal_name in ORIENTATION_MAP.items():
            if internal_name == self._settings.orientation:
                self._orientation_combo.setCurrentText(display_name)
                break

        self._refresh_spin.setValue(self._settings.refresh_rate)
        self._auto_brightness.setChecked(self._settings.auto_brightness)
        self._brightness_slider.setValue(self._settings.brightness_max)
        self._brightness_label.setText(str(self._settings.brightness_max))

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        profile = self._profile_combo.currentText()
        self._settings.profile = profile
        self._settings.width = self._width_spin.value()
        self._settings.height = self._height_spin.value()

        orientation_display = self._orientation_combo.currentText()
        self._settings.orientation = ORIENTATION_MAP.get(orientation_display, "landscape")

        self._settings.refresh_rate = self._refresh_spin.value()
        self._settings.auto_brightness = self._auto_brightness.isChecked()
        self._settings.brightness_max = self._brightness_slider.value()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._profile_combo.setCurrentText("1024x600")
        self._width_spin.setValue(1024)
        self._height_spin.setValue(600)
        self._orientation_combo.setCurrentText("Landscape")
        self._refresh_spin.setValue(60)
        self._auto_brightness.setChecked(True)
        self._brightness_slider.setValue(700)
