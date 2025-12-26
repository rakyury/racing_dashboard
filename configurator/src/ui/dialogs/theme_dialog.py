# Theme Settings Dialog
"""Dialog for configuring theme settings."""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QFrame, QGridLayout, QPushButton, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import ThemeSettings


# Theme presets inspired by MoTeC, EcuMaster, Haltech
THEME_PRESETS = [
    "Motec Dark",
    "Motec Light",
    "EcuMaster Dark",
    "EcuMaster Blue",
    "Haltech IQ3",
    "Haltech Pro",
    "Night Mode",
    "Racing Green",
    "Carbon Fiber",
    "Custom",
]


class ThemePreview(QFrame):
    """Widget showing theme color preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        self._bg_color = QColor(30, 30, 30)
        self._text_color = QColor(255, 255, 255)
        self._accent_color = QColor(0, 120, 215)
        self._gauge_color = QColor(60, 180, 60)

    def set_colors(self, bg: QColor, text: QColor, accent: QColor, gauge: QColor) -> None:
        """Set preview colors."""
        self._bg_color = bg
        self._text_color = text
        self._accent_color = accent
        self._gauge_color = gauge
        self.update()

    def paintEvent(self, event) -> None:
        """Paint theme preview."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Background
        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(QPen(self._accent_color, 2))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        # Mini gauge
        gauge_rect = rect.adjusted(10, 10, -rect.width() // 2 - 5, -40)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(self._gauge_color, 4))
        painter.drawArc(gauge_rect, 30 * 16, 120 * 16)

        # Text
        painter.setPen(QPen(self._text_color))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect.adjusted(110, 15, -10, 0), Qt.AlignmentFlag.AlignLeft, "8200")

        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(rect.adjusted(110, 35, -10, 0), Qt.AlignmentFlag.AlignLeft, "RPM")

        # Accent bar
        painter.setBrush(QBrush(self._accent_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, rect.height() - 20, rect.width() - 20, 10, 3, 3)


class ColorButton(QPushButton):
    """Button that shows and allows selecting a color."""

    def __init__(self, color: QColor = QColor(255, 255, 255), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(40, 25)
        self.setStyleSheet(self._get_style())
        self.clicked.connect(self._pick_color)

    def _get_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 2px solid #555;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #0078d4;
            }}
        """

    def color(self) -> QColor:
        return self._color

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.setStyleSheet(self._get_style())

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Select Color")
        if color.isValid():
            self._color = color
            self.setStyleSheet(self._get_style())


class ThemeSettingsDialog(BaseSettingsDialog):
    """Dialog for theme settings."""

    def __init__(self, settings: ThemeSettings, parent=None):
        self._settings = settings
        super().__init__("Theme Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Theme Selection Group
        theme_group = self._create_group("Theme Preset")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setContentsMargins(12, 20, 12, 12)
        theme_layout.setSpacing(12)

        # Preset selector
        self._preset_combo = self._create_combobox(THEME_PRESETS)
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        theme_layout.addWidget(SettingsRow(
            "Active Theme:",
            self._preset_combo,
            "Select from built-in themes"
        ))

        # Preview
        preview_widget = QWidget()
        preview_layout = QHBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 10, 0, 0)

        self._preview = ThemePreview()
        preview_layout.addWidget(self._preview)
        preview_layout.addStretch()

        theme_layout.addWidget(preview_widget)

        self._content_layout.addWidget(theme_group)

        # Auto Night Mode Group
        night_group = self._create_group("Auto Night Mode")
        night_layout = QVBoxLayout(night_group)
        night_layout.setContentsMargins(12, 20, 12, 12)
        night_layout.setSpacing(8)

        self._auto_night = self._create_checkbox("Enable auto night mode", True)
        self._auto_night.stateChanged.connect(self._on_auto_night_changed)
        night_layout.addWidget(self._auto_night)

        # Day theme
        self._day_theme_combo = self._create_combobox(THEME_PRESETS[:-1])
        night_layout.addWidget(SettingsRow("Day Theme:", self._day_theme_combo))

        # Night theme
        self._night_theme_combo = self._create_combobox(THEME_PRESETS[:-1])
        night_layout.addWidget(SettingsRow("Night Theme:", self._night_theme_combo))

        # Time settings
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)

        self._night_start_spin = self._create_spinbox(0, 23, 20, ":00")
        time_layout.addWidget(self._night_start_spin)

        time_layout.addWidget(QLabel("to"))

        self._night_end_spin = self._create_spinbox(0, 23, 6, ":00")
        time_layout.addWidget(self._night_end_spin)

        time_layout.addStretch()

        night_layout.addWidget(SettingsRow(
            "Night Hours:",
            time_widget,
            "Time range for night mode"
        ))

        self._content_layout.addWidget(night_group)

        # Brightness Group
        brightness_group = self._create_group("Theme Brightness")
        brightness_layout = QVBoxLayout(brightness_group)
        brightness_layout.setContentsMargins(12, 20, 12, 12)
        brightness_layout.setSpacing(8)

        # Brightness multiplier
        brightness_widget = QWidget()
        brightness_inner = QHBoxLayout(brightness_widget)
        brightness_inner.setContentsMargins(0, 0, 0, 0)
        brightness_inner.setSpacing(12)

        self._brightness_slider = self._create_slider(50, 150, 100)
        self._brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_inner.addWidget(self._brightness_slider)

        self._brightness_label = QLabel("100%")
        self._brightness_label.setStyleSheet("color: #fff; min-width: 50px;")
        brightness_inner.addWidget(self._brightness_label)

        brightness_layout.addWidget(SettingsRow(
            "Brightness:",
            brightness_widget,
            "Adjust overall theme brightness"
        ))

        self._content_layout.addWidget(brightness_group)

    def _on_preset_changed(self, preset: str) -> None:
        """Handle preset change."""
        # Update preview based on preset
        presets = {
            "Motec Dark": (QColor(25, 25, 25), QColor(255, 255, 255), QColor(255, 100, 0), QColor(255, 100, 0)),
            "Motec Light": (QColor(230, 230, 230), QColor(30, 30, 30), QColor(255, 80, 0), QColor(200, 50, 0)),
            "EcuMaster Dark": (QColor(20, 25, 30), QColor(220, 220, 220), QColor(0, 180, 255), QColor(0, 200, 100)),
            "EcuMaster Blue": (QColor(15, 30, 50), QColor(200, 220, 255), QColor(0, 150, 255), QColor(100, 200, 255)),
            "Haltech IQ3": (QColor(0, 0, 0), QColor(255, 255, 255), QColor(255, 50, 50), QColor(50, 255, 50)),
            "Haltech Pro": (QColor(10, 10, 10), QColor(230, 230, 230), QColor(220, 40, 40), QColor(40, 200, 40)),
            "Night Mode": (QColor(10, 10, 10), QColor(150, 50, 50), QColor(100, 30, 30), QColor(80, 20, 20)),
            "Racing Green": (QColor(20, 30, 20), QColor(180, 220, 180), QColor(50, 180, 50), QColor(80, 200, 80)),
            "Carbon Fiber": (QColor(40, 40, 45), QColor(200, 200, 200), QColor(100, 100, 100), QColor(150, 150, 150)),
        }

        if preset in presets:
            bg, text, accent, gauge = presets[preset]
            self._preview.set_colors(bg, text, accent, gauge)

    def _on_auto_night_changed(self, state: int) -> None:
        """Handle auto night mode toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._day_theme_combo.setEnabled(enabled)
        self._night_theme_combo.setEnabled(enabled)
        self._night_start_spin.setEnabled(enabled)
        self._night_end_spin.setEnabled(enabled)

    def _on_brightness_changed(self, value: int) -> None:
        """Update brightness label."""
        self._brightness_label.setText(f"{value}%")

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._preset_combo.setCurrentText(self._settings.active_preset)
        self._auto_night.setChecked(self._settings.auto_night_mode)
        self._day_theme_combo.setCurrentText(self._settings.day_theme)
        self._night_theme_combo.setCurrentText(self._settings.night_theme)
        self._night_start_spin.setValue(self._settings.night_mode_start)
        self._night_end_spin.setValue(self._settings.night_mode_end)
        self._brightness_slider.setValue(int(self._settings.brightness_multiplier * 100))
        self._brightness_label.setText(f"{int(self._settings.brightness_multiplier * 100)}%")

        self._on_preset_changed(self._settings.active_preset)
        self._on_auto_night_changed(Qt.CheckState.Checked.value if self._settings.auto_night_mode else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.active_preset = self._preset_combo.currentText()
        self._settings.auto_night_mode = self._auto_night.isChecked()
        self._settings.day_theme = self._day_theme_combo.currentText()
        self._settings.night_theme = self._night_theme_combo.currentText()
        self._settings.night_mode_start = self._night_start_spin.value()
        self._settings.night_mode_end = self._night_end_spin.value()
        self._settings.brightness_multiplier = self._brightness_slider.value() / 100.0

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._preset_combo.setCurrentText("Motec Dark")
        self._auto_night.setChecked(True)
        self._day_theme_combo.setCurrentText("Motec Dark")
        self._night_theme_combo.setCurrentText("Night Mode")
        self._night_start_spin.setValue(20)
        self._night_end_spin.setValue(6)
        self._brightness_slider.setValue(100)
