# Widget Palette
"""Palette of draggable widgets for the screen editor."""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QToolButton, QSizePolicy, QGridLayout,
    QGroupBox
)
from PyQt6.QtCore import Qt, QMimeData, QSize, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont

from models.widget_types import (
    WidgetType, WidgetDefinition, WIDGET_DEFINITIONS,
    get_widgets_by_category
)

logger = logging.getLogger(__name__)


class WidgetButton(QToolButton):
    """A draggable button representing a widget type."""

    def __init__(self, widget_def: WidgetDefinition, parent=None):
        super().__init__(parent)
        self._widget_def = widget_def
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup button appearance."""
        self.setText(self._widget_def.display_name)
        self.setToolTip(self._widget_def.description)
        # Icon on left, text on right
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(32, 32))
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create icon as colored rectangle
        pixmap = self._create_icon()
        from PyQt6.QtGui import QIcon
        self.setIcon(QIcon(pixmap))

        # Styling
        self.setStyleSheet("""
            QToolButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ddd;
                font-size: 11px;
                text-align: left;
            }
            QToolButton:hover {
                background-color: #4d4d4d;
                border-color: #0078d4;
            }
            QToolButton:pressed {
                background-color: #2d2d2d;
            }
        """)

    def _create_icon(self) -> QPixmap:
        """Create a colored icon for the widget type."""
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Color based on widget type
        colors = {
            # Gauges
            WidgetType.RPM_GAUGE: QColor(60, 120, 60),
            WidgetType.SPEEDOMETER: QColor(60, 60, 120),
            WidgetType.TEMP_GAUGE: QColor(120, 80, 50),
            WidgetType.FUEL_GAUGE: QColor(100, 80, 60),
            WidgetType.PRESSURE_GAUGE: QColor(90, 90, 60),
            WidgetType.BOOST_GAUGE: QColor(60, 100, 120),
            # Indicators
            WidgetType.GEAR_INDICATOR: QColor(120, 90, 60),
            WidgetType.SHIFT_LIGHTS: QColor(120, 60, 60),
            WidgetType.STATUS_PILL: QColor(60, 100, 100),
            WidgetType.WARNING_LIGHT: QColor(120, 50, 50),
            WidgetType.LED_INDICATOR: QColor(50, 120, 50),
            # Meters
            WidgetType.G_FORCE_METER: QColor(80, 80, 120),
            WidgetType.THROTTLE_BAR: QColor(50, 120, 50),
            WidgetType.BRAKE_BAR: QColor(120, 50, 50),
            WidgetType.AFR_BAR: QColor(100, 80, 100),
            # Timers
            WidgetType.LAP_TIMER: QColor(80, 80, 80),
            WidgetType.DELTA_DISPLAY: QColor(100, 80, 80),
            WidgetType.SECTOR_TIMES: QColor(80, 80, 100),
            WidgetType.BEST_LAP: QColor(120, 60, 120),
            # Text
            WidgetType.CUSTOM_TEXT: QColor(100, 100, 100),
            WidgetType.VARIABLE_DISPLAY: QColor(70, 90, 110),
            WidgetType.NUMERIC_DISPLAY: QColor(80, 100, 100),
            # Graphics
            WidgetType.IMAGE: QColor(80, 80, 80),
            WidgetType.RECTANGLE: QColor(70, 70, 70),
            WidgetType.LINE: QColor(60, 60, 60),
        }

        color = colors.get(self._widget_def.widget_type, QColor(80, 80, 80))
        painter.setBrush(color)
        painter.setPen(QColor(150, 150, 150))

        # Draw shape based on category
        if self._widget_def.category == "Gauges":
            # Circle for gauges
            painter.drawEllipse(4, 4, size - 8, size - 8)
        elif self._widget_def.category == "Indicators":
            # Rounded rect for indicators
            painter.drawRoundedRect(4, 4, size - 8, size - 8, 8, 8)
        elif self._widget_def.category == "Meters":
            # Horizontal bar for meters
            painter.drawRect(4, 12, size - 8, size - 24)
        elif self._widget_def.category == "Timers":
            # Rectangle with text area
            painter.drawRoundedRect(4, 8, size - 8, size - 16, 4, 4)
        elif self._widget_def.category == "Text":
            # Text icon shape
            painter.drawRoundedRect(4, 10, size - 8, size - 20, 2, 2)
        elif self._widget_def.category == "Graphics":
            # Diamond shape for graphics
            from PyQt6.QtGui import QPolygon
            from PyQt6.QtCore import QPoint
            points = [QPoint(size // 2, 4), QPoint(size - 4, size // 2),
                     QPoint(size // 2, size - 4), QPoint(4, size // 2)]
            painter.drawPolygon(QPolygon(points))
        else:
            # Default square
            painter.drawRect(4, 4, size - 8, size - 8)

        # Add type initial
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)

        initial = self._widget_def.display_name[0]
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial)

        painter.end()
        return pixmap

    def mousePressEvent(self, event) -> None:
        """Handle mouse press to start drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_drag()
        super().mousePressEvent(event)

    def _start_drag(self) -> None:
        """Start a drag operation."""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self._widget_def.widget_type.value)
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = self._create_drag_pixmap()
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        drag.exec(Qt.DropAction.CopyAction)

    def _create_drag_pixmap(self) -> QPixmap:
        """Create pixmap for drag operation."""
        width = self._widget_def.default_width
        height = self._widget_def.default_height

        # Scale down for preview
        scale = 0.5
        width = int(width * scale)
        height = int(height * scale)

        pixmap = QPixmap(width, height)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.setBrush(QColor(60, 60, 60, 200))
        painter.setPen(QColor(0, 120, 215))
        painter.drawRoundedRect(0, 0, width, height, 4, 4)

        # Text
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter,
                        self._widget_def.display_name)

        painter.end()
        return pixmap


class WidgetPalette(QWidget):
    """
    Palette panel containing all available widgets organized by category.
    Widgets can be dragged onto the canvas.
    """

    widget_selected = pyqtSignal(object)  # WidgetDefinition

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the palette UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("Widgets")
        header.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #fff;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(header)

        # Scroll area for widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
        """)

        # Container for widget groups
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(12)

        # Add widgets by category
        categories = get_widgets_by_category()

        for category_name, definitions in categories.items():
            group = self._create_category_group(category_name, definitions)
            container_layout.addWidget(group)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_category_group(self, name: str, definitions: list) -> QGroupBox:
        """Create a collapsible group for a widget category."""
        group = QGroupBox(name)
        group.setStyleSheet("""
            QGroupBox {
                color: #aaa;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        # Single column layout for full-width buttons
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(4)

        for definition in definitions:
            button = WidgetButton(definition)
            button.clicked.connect(lambda checked, d=definition: self._on_widget_clicked(d))
            layout.addWidget(button)

        return group

    def _on_widget_clicked(self, definition: WidgetDefinition) -> None:
        """Handle widget button click."""
        logger.debug(f"Widget clicked: {definition.display_name}")
        self.widget_selected.emit(definition)


class CompactWidgetPalette(QWidget):
    """
    Compact horizontal widget palette for toolbar integration.
    """

    widget_selected = pyqtSignal(object)  # WidgetDefinition

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup compact palette."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Label
        label = QLabel("Add:")
        label.setStyleSheet("color: #888;")
        layout.addWidget(label)

        # Common widgets as quick buttons
        common_widgets = [
            WidgetType.RPM_GAUGE,
            WidgetType.SPEEDOMETER,
            WidgetType.GEAR_INDICATOR,
            WidgetType.SHIFT_LIGHTS,
            WidgetType.TEMP_GAUGE,
            WidgetType.G_FORCE_METER,
            WidgetType.LAP_TIMER,
            WidgetType.CUSTOM_TEXT,
        ]

        for widget_type in common_widgets:
            definition = WIDGET_DEFINITIONS.get(widget_type)
            if definition:
                btn = QToolButton()
                btn.setText(definition.display_name[:3])
                btn.setToolTip(definition.display_name)
                btn.setMinimumSize(40, 30)
                btn.setStyleSheet("""
                    QToolButton {
                        background-color: #3d3d3d;
                        border: 1px solid #555;
                        border-radius: 3px;
                        color: #ddd;
                        font-size: 10px;
                        padding: 2px 4px;
                    }
                    QToolButton:hover {
                        background-color: #4d4d4d;
                        border-color: #0078d4;
                    }
                """)
                btn.clicked.connect(lambda checked, d=definition: self.widget_selected.emit(d))
                layout.addWidget(btn)

        layout.addStretch()
