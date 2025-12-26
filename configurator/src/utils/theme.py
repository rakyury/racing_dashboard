# Theme Manager
"""Dark/Light theme management for the configurator."""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


class ThemeManager:
    """Manages application themes."""

    # Dark theme colors (Fluent Design inspired)
    DARK_COLORS = {
        "window": "#1e1e1e",
        "window_text": "#ffffff",
        "base": "#2d2d2d",
        "alternate_base": "#353535",
        "text": "#ffffff",
        "button": "#3d3d3d",
        "button_text": "#ffffff",
        "bright_text": "#ff0000",
        "highlight": "#0078d4",
        "highlight_text": "#ffffff",
        "link": "#0078d4",
        "disabled_text": "#808080",
        "disabled_button": "#2d2d2d",
        "tooltip_base": "#2d2d2d",
        "tooltip_text": "#ffffff",
        "border": "#555555",
        "success": "#107c10",
        "warning": "#ff8c00",
        "error": "#e81123",
    }

    # Light theme colors
    LIGHT_COLORS = {
        "window": "#f3f3f3",
        "window_text": "#000000",
        "base": "#ffffff",
        "alternate_base": "#f5f5f5",
        "text": "#000000",
        "button": "#e1e1e1",
        "button_text": "#000000",
        "bright_text": "#ff0000",
        "highlight": "#0078d4",
        "highlight_text": "#ffffff",
        "link": "#0078d4",
        "disabled_text": "#a0a0a0",
        "disabled_button": "#f0f0f0",
        "tooltip_base": "#ffffff",
        "tooltip_text": "#000000",
        "border": "#cccccc",
        "success": "#107c10",
        "warning": "#ff8c00",
        "error": "#e81123",
    }

    def __init__(self):
        self._current_theme = "dark"

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def apply_dark_theme(self, app: QApplication) -> None:
        """Apply dark theme to the application."""
        self._current_theme = "dark"
        self._apply_theme(app, self.DARK_COLORS)
        app.setStyle("Fusion")

    def apply_light_theme(self, app: QApplication) -> None:
        """Apply light theme to the application."""
        self._current_theme = "light"
        self._apply_theme(app, self.LIGHT_COLORS)
        app.setStyle("Fusion")

    def toggle_theme(self, app: QApplication) -> None:
        """Toggle between dark and light themes."""
        if self._current_theme == "dark":
            self.apply_light_theme(app)
        else:
            self.apply_dark_theme(app)

    def _apply_theme(self, app: QApplication, colors: dict) -> None:
        """Apply a color scheme to the application."""
        palette = QPalette()

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["window_text"]))

        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["base"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["alternate_base"]))

        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["bright_text"]))

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["button_text"]))

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["highlight_text"]))

        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["link"]))

        # Disabled colors
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(colors["disabled_text"])
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(colors["disabled_text"])
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Button,
            QColor(colors["disabled_button"])
        )

        # Tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["tooltip_base"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["tooltip_text"]))

        app.setPalette(palette)

        # Additional stylesheet for borders and custom styling
        stylesheet = f"""
            QToolTip {{
                color: {colors["tooltip_text"]};
                background-color: {colors["tooltip_base"]};
                border: 1px solid {colors["border"]};
                padding: 4px;
            }}

            QGroupBox {{
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}

            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                border-radius: 4px;
            }}

            QDockWidget {{
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }}

            QDockWidget::title {{
                background: {colors["alternate_base"]};
                padding: 6px;
            }}

            QScrollBar:vertical {{
                border: none;
                background: {colors["base"]};
                width: 12px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background: {colors["button"]};
                min-height: 20px;
                border-radius: 6px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QStatusBar {{
                background: {colors["alternate_base"]};
                border-top: 1px solid {colors["border"]};
            }}
        """

        app.setStyleSheet(stylesheet)

    def get_color(self, name: str) -> str:
        """Get a color from the current theme."""
        colors = self.DARK_COLORS if self._current_theme == "dark" else self.LIGHT_COLORS
        return colors.get(name, "#ffffff")
