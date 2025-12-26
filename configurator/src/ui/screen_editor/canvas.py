# Screen Editor Canvas
"""Main canvas for visual screen editing using QGraphicsScene/QGraphicsView."""

import logging
from typing import Optional, List, Dict, Any
import copy
import json

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem,
    QMenu, QWidget, QVBoxLayout, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSizeF, QMimeData
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QWheelEvent,
    QKeyEvent, QContextMenuEvent, QTransform, QClipboard
)

from models.screen_layout import ScreenLayout, WidgetConfig
from models.widget_types import WidgetType, get_widget_definition

logger = logging.getLogger(__name__)


class GridOverlay(QGraphicsRectItem):
    """Grid overlay for snapping and visual guidance."""

    def __init__(self, width: int, height: int, columns: int, rows: int):
        super().__init__(0, 0, width, height)
        self._columns = columns
        self._rows = rows
        self._visible = True
        self.setZValue(-1000)  # Behind everything
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def paint(self, painter: QPainter, option, widget) -> None:
        if not self._visible:
            return

        rect = self.rect()
        cell_w = rect.width() / self._columns
        cell_h = rect.height() / self._rows

        # Grid lines - more visible
        pen = QPen(QColor(80, 80, 80, 100), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        # Vertical lines
        for i in range(1, self._columns):
            x = i * cell_w
            painter.drawLine(QPointF(x, 0), QPointF(x, rect.height()))

        # Horizontal lines
        for i in range(1, self._rows):
            y = i * cell_h
            painter.drawLine(QPointF(0, y), QPointF(rect.width(), y))

        # Center lines - more prominent
        pen = QPen(QColor(100, 100, 100, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(rect.width() / 2, 0), QPointF(rect.width() / 2, rect.height()))
        painter.drawLine(QPointF(0, rect.height() / 2), QPointF(rect.width(), rect.height() / 2))

        # Border
        pen = QPen(QColor(100, 100, 100), 2)
        painter.setPen(pen)
        painter.drawRect(rect)

    def set_grid_visible(self, visible: bool) -> None:
        self._visible = visible
        self.update()


class WidgetItem(QGraphicsRectItem):
    """A draggable, resizable widget item on the canvas."""

    HANDLE_SIZE = 8
    MIN_SIZE = 20

    def __init__(self, widget_config: WidgetConfig, parent=None):
        super().__init__(parent)
        self._config = widget_config
        self._is_selected = False
        self._resize_handle = None
        self._drag_start = None
        self._preview_mode = False
        self._preview_values: Dict[int, float] = {}  # channel_id -> value

        # Set position and size from config
        self.setRect(0, 0, widget_config.width, widget_config.height)
        self.setPos(widget_config.x, widget_config.y)
        self.setZValue(widget_config.z_index)

        # Enable interaction
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        # Get widget definition for rendering
        self._definition = get_widget_definition(widget_config.widget_type)

    @property
    def config(self) -> WidgetConfig:
        return self._config

    @property
    def widget_id(self) -> str:
        return self._config.id

    def paint(self, painter: QPainter, option, widget) -> None:
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.setBrush(QBrush(QColor(35, 35, 35)))
        if self.isSelected():
            pen = QPen(QColor(0, 120, 215), 3)
        else:
            pen = QPen(QColor(80, 80, 80), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 4, 4)

        # Draw widget-specific preview
        content_rect = rect.adjusted(4, 4, -4, -4)
        self._draw_widget_preview(painter, content_rect)

        # Draw label at bottom
        label_height = min(20, rect.height() * 0.15)
        label_rect = QRectF(rect.left(), rect.bottom() - label_height, rect.width(), label_height)
        painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(label_rect, 0, 0)

        # Label text
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        name = self._config.name or self._config.widget_type.value.replace("_", " ").title()
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, name)

        # Draw resize handles if selected
        if self.isSelected():
            self._draw_resize_handles(painter)

    def _draw_widget_preview(self, painter: QPainter, rect: QRectF) -> None:
        """Draw widget-specific visual preview."""
        wtype = self._config.widget_type

        if wtype == WidgetType.RPM_GAUGE:
            self._draw_rpm_gauge(painter, rect)
        elif wtype == WidgetType.SPEEDOMETER:
            self._draw_speedometer(painter, rect)
        elif wtype == WidgetType.GEAR_INDICATOR:
            self._draw_gear_indicator(painter, rect)
        elif wtype == WidgetType.SHIFT_LIGHTS:
            self._draw_shift_lights(painter, rect)
        elif wtype == WidgetType.TEMP_GAUGE:
            self._draw_temp_gauge(painter, rect)
        elif wtype == WidgetType.G_FORCE_METER:
            self._draw_g_force_meter(painter, rect)
        elif wtype == WidgetType.LAP_TIMER:
            self._draw_lap_timer(painter, rect)
        elif wtype == WidgetType.STATUS_PILL:
            self._draw_status_pill(painter, rect)
        elif wtype == WidgetType.CUSTOM_TEXT:
            self._draw_custom_text(painter, rect)
        elif wtype == WidgetType.FUEL_GAUGE:
            self._draw_fuel_gauge(painter, rect)
        elif wtype == WidgetType.VARIABLE_DISPLAY:
            self._draw_variable_display(painter, rect)
        elif wtype == WidgetType.LINE_GRAPH:
            self._draw_line_graph(painter, rect)
        elif wtype == WidgetType.BAR_CHART:
            self._draw_bar_chart(painter, rect)
        elif wtype == WidgetType.HISTOGRAM:
            self._draw_histogram(painter, rect)
        elif wtype == WidgetType.PIE_CHART:
            self._draw_pie_chart(painter, rect)

    def _draw_rpm_gauge(self, painter: QPainter, rect: QRectF) -> None:
        """Draw RPM gauge preview."""
        import math
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.4

        # Get RPM value (channel 100)
        rpm = self._get_preview_value(100, 6200)
        max_rpm = 9000

        # Draw arc background
        painter.setPen(QPen(QColor(60, 60, 60), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        arc_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawArc(arc_rect, 220 * 16, -260 * 16)

        # Draw green zone
        painter.setPen(QPen(QColor(50, 180, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(arc_rect, 220 * 16, -180 * 16)

        # Draw yellow zone
        painter.setPen(QPen(QColor(220, 180, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(arc_rect, 40 * 16, -40 * 16)

        # Draw red zone
        painter.setPen(QPen(QColor(220, 50, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(arc_rect, 0 * 16, -40 * 16)

        # Draw needle based on RPM
        rpm_ratio = min(1.0, max(0.0, rpm / max_rpm))
        needle_angle = 220 - (rpm_ratio * 260)  # 220 to -40 degrees
        angle = math.radians(needle_angle)
        needle_len = radius * 0.85
        end_x = center.x() + needle_len * math.cos(angle)
        end_y = center.y() - needle_len * math.sin(angle)
        painter.setPen(QPen(QColor(255, 100, 100), 3))
        painter.drawLine(center, QPointF(end_x, end_y))

        # Draw center cap
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 0.12, radius * 0.12)

        # Draw value
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(max(10, int(radius * 0.25)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(center.x() - radius, center.y() + radius * 0.2, radius * 2, radius * 0.5),
                        Qt.AlignmentFlag.AlignCenter, f"{int(rpm)}")

    def _draw_speedometer(self, painter: QPainter, rect: QRectF) -> None:
        """Draw speedometer preview."""
        import math
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.4

        # Get speed value (channel 101)
        speed = self._get_preview_value(101, 127)
        max_speed = 300

        # Draw arc
        painter.setPen(QPen(QColor(50, 80, 180), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        arc_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawArc(arc_rect, 220 * 16, -260 * 16)

        # Draw tick marks
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        for i in range(0, 280, 40):
            angle = math.radians(220 - i)
            inner_r = radius * 0.75
            outer_r = radius * 0.95
            x1 = center.x() + inner_r * math.cos(angle)
            y1 = center.y() - inner_r * math.sin(angle)
            x2 = center.x() + outer_r * math.cos(angle)
            y2 = center.y() - outer_r * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Draw needle based on speed
        speed_ratio = min(1.0, max(0.0, speed / max_speed))
        needle_angle = 220 - (speed_ratio * 260)
        angle = math.radians(needle_angle)
        needle_len = radius * 0.8
        end_x = center.x() + needle_len * math.cos(angle)
        end_y = center.y() - needle_len * math.sin(angle)
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(center, QPointF(end_x, end_y))

        # Draw center
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 0.1, radius * 0.1)

        # Draw value
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(max(12, int(radius * 0.3)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(center.x() - radius, center.y() + radius * 0.15, radius * 2, radius * 0.5),
                        Qt.AlignmentFlag.AlignCenter, f"{int(speed)}")

        # Draw unit
        font.setPointSize(max(8, int(radius * 0.15)))
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRectF(center.x() - radius, center.y() + radius * 0.5, radius * 2, radius * 0.3),
                        Qt.AlignmentFlag.AlignCenter, "km/h")

    def _draw_gear_indicator(self, painter: QPainter, rect: QRectF) -> None:
        """Draw gear indicator preview."""
        # Get gear value (channel 110)
        gear = int(self._get_preview_value(110, 3))
        gear_text = "N" if gear == 0 else str(gear)

        # Background
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.setPen(QPen(QColor(100, 80, 40), 2))
        painter.drawRoundedRect(rect, 8, 8)

        # Gear number
        painter.setPen(QPen(QColor(255, 200, 100)))
        font = painter.font()
        font.setPointSize(max(24, int(min(rect.width(), rect.height()) * 0.6)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, gear_text)

    def _draw_shift_lights(self, painter: QPainter, rect: QRectF) -> None:
        """Draw shift lights preview."""
        led_count = self._config.properties.get("led_count", 10)
        spacing = rect.width() / (led_count + 1)
        led_size = min(spacing * 0.7, rect.height() * 0.5)
        y = rect.center().y()

        # Get RPM and calculate how many LEDs to light
        rpm = self._get_preview_value(100, 6000)
        shift_rpm = 7500
        light_rpm = 4500
        rpm_per_led = (shift_rpm - light_rpm) / led_count
        leds_lit = int((rpm - light_rpm) / rpm_per_led) if rpm > light_rpm else 0

        for i in range(led_count):
            x = rect.left() + spacing * (i + 1)
            lit = i < leds_lit

            # Color gradient: green -> yellow -> red
            if i < led_count * 0.4:
                color = QColor(50, 200, 50) if lit else QColor(30, 60, 30)
            elif i < led_count * 0.7:
                color = QColor(220, 200, 50) if lit else QColor(60, 55, 30)
            else:
                color = QColor(220, 50, 50) if lit else QColor(60, 30, 30)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawEllipse(QPointF(x, y), led_size / 2, led_size / 2)

    def _draw_temp_gauge(self, painter: QPainter, rect: QRectF) -> None:
        """Draw temperature gauge preview."""
        # Vertical bar gauge
        bar_width = rect.width() * 0.3
        bar_rect = QRectF(rect.center().x() - bar_width / 2, rect.top() + 10,
                         bar_width, rect.height() - 40)

        # Background
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(bar_rect, 4, 4)

        # Fill level (70%)
        fill_height = bar_rect.height() * 0.7
        fill_rect = QRectF(bar_rect.left(), bar_rect.bottom() - fill_height,
                          bar_rect.width(), fill_height)

        # Gradient from blue to red
        gradient = QColor(200, 120, 50)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(fill_rect, 4, 4)

        # Temperature value
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(max(10, int(rect.height() * 0.12)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.bottom() - 25, rect.width(), 20),
                        Qt.AlignmentFlag.AlignCenter, "92°C")

    def _draw_g_force_meter(self, painter: QPainter, rect: QRectF) -> None:
        """Draw G-force meter preview."""
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.4

        # Get G values (channels 123=lateral, 124=longitudinal)
        g_lat = self._get_preview_value(123, 0.3)
        g_lon = self._get_preview_value(124, 0.2)
        max_g = 2.0

        # Draw circles
        for r in [radius, radius * 0.66, radius * 0.33]:
            painter.setPen(QPen(QColor(60, 60, 80), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, r, r)

        # Draw cross
        painter.setPen(QPen(QColor(60, 60, 80), 1))
        painter.drawLine(QPointF(center.x() - radius, center.y()),
                        QPointF(center.x() + radius, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - radius),
                        QPointF(center.x(), center.y() + radius))

        # Draw G dot based on data
        g_x = center.x() + (g_lat / max_g) * radius
        g_y = center.y() - (g_lon / max_g) * radius
        # Clamp to circle
        dx = g_x - center.x()
        dy = g_y - center.y()
        dist = (dx*dx + dy*dy) ** 0.5
        if dist > radius:
            g_x = center.x() + dx * radius / dist
            g_y = center.y() + dy * radius / dist

        painter.setBrush(QBrush(QColor(100, 150, 255)))
        painter.setPen(QPen(QColor(150, 200, 255), 2))
        painter.drawEllipse(QPointF(g_x, g_y), 8, 8)

    def _draw_lap_timer(self, painter: QPainter, rect: QRectF) -> None:
        """Draw lap timer preview."""
        # Get lap timer values
        lap_time = self._get_preview_value(550, 83.456)
        best_lap = self._get_preview_value(552, 82.891)
        delta = self._get_preview_value(553, -0.342)

        # Format time
        def format_time(seconds):
            mins = int(seconds) // 60
            secs = seconds - mins * 60
            return f"{mins}:{secs:06.3f}"

        # Background
        painter.setBrush(QBrush(QColor(25, 25, 25)))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Current lap time
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(max(14, int(rect.height() * 0.25)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.top() + rect.height() * 0.1,
                               rect.width(), rect.height() * 0.4),
                        Qt.AlignmentFlag.AlignCenter, format_time(lap_time))

        # Delta (green = faster, red = slower)
        delta_color = QColor(50, 220, 50) if delta < 0 else QColor(220, 50, 50)
        painter.setPen(QPen(delta_color))
        font.setPointSize(max(10, int(rect.height() * 0.15)))
        painter.setFont(font)
        delta_str = f"{delta:+.3f}"
        painter.drawText(QRectF(rect.left(), rect.top() + rect.height() * 0.5,
                               rect.width(), rect.height() * 0.25),
                        Qt.AlignmentFlag.AlignCenter, delta_str)

        # Best lap
        painter.setPen(QPen(QColor(150, 150, 150)))
        font.setPointSize(max(8, int(rect.height() * 0.1)))
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.top() + rect.height() * 0.75,
                               rect.width(), rect.height() * 0.2),
                        Qt.AlignmentFlag.AlignCenter, f"Best: {format_time(best_lap)}")

    def _draw_status_pill(self, painter: QPainter, rect: QRectF) -> None:
        """Draw status pill preview."""
        # Pill shape
        painter.setBrush(QBrush(QColor(50, 150, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        pill_rect = QRectF(rect.left() + rect.width() * 0.1, rect.top() + rect.height() * 0.25,
                          rect.width() * 0.8, rect.height() * 0.5)
        painter.drawRoundedRect(pill_rect, pill_rect.height() / 2, pill_rect.height() / 2)

        # Status text
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(max(9, int(rect.height() * 0.2)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, "OK")

    def _draw_custom_text(self, painter: QPainter, rect: QRectF) -> None:
        """Draw custom text preview."""
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = painter.font()
        font.setPointSize(max(12, int(rect.height() * 0.3)))
        painter.setFont(font)
        text = self._config.properties.get("text", "Custom Text")
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_fuel_gauge(self, painter: QPainter, rect: QRectF) -> None:
        """Draw fuel gauge preview."""
        # Horizontal bar
        bar_height = rect.height() * 0.3
        bar_rect = QRectF(rect.left() + 10, rect.center().y() - bar_height / 2,
                         rect.width() - 20, bar_height)

        # Background
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(bar_rect, 4, 4)

        # Fill (60%)
        fill_width = bar_rect.width() * 0.6
        fill_rect = QRectF(bar_rect.left(), bar_rect.top(), fill_width, bar_rect.height())
        painter.setBrush(QBrush(QColor(200, 150, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(fill_rect, 4, 4)

        # Labels
        painter.setPen(QPen(QColor(150, 150, 150)))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(QRectF(bar_rect.left(), bar_rect.bottom() + 2, 20, 15),
                        Qt.AlignmentFlag.AlignLeft, "E")
        painter.drawText(QRectF(bar_rect.right() - 20, bar_rect.bottom() + 2, 20, 15),
                        Qt.AlignmentFlag.AlignRight, "F")

        # Fuel icon
        painter.setPen(QPen(QColor(200, 200, 200)))
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.3),
                        Qt.AlignmentFlag.AlignCenter, "⛽")

    def _draw_variable_display(self, painter: QPainter, rect: QRectF) -> None:
        """Draw variable display preview."""
        # Label
        painter.setPen(QPen(QColor(150, 150, 150)))
        font = painter.font()
        font.setPointSize(max(8, int(rect.height() * 0.15)))
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.top() + 5, rect.width(), rect.height() * 0.25),
                        Qt.AlignmentFlag.AlignCenter, "Oil Pressure")

        # Value
        painter.setPen(QPen(QColor(100, 180, 255)))
        font.setPointSize(max(16, int(rect.height() * 0.35)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.center().y() - rect.height() * 0.2,
                               rect.width(), rect.height() * 0.4),
                        Qt.AlignmentFlag.AlignCenter, "4.2")

        # Unit
        painter.setPen(QPen(QColor(150, 150, 150)))
        font.setPointSize(max(8, int(rect.height() * 0.12)))
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.bottom() - rect.height() * 0.25,
                               rect.width(), rect.height() * 0.2),
                        Qt.AlignmentFlag.AlignCenter, "bar")

    def _draw_line_graph(self, painter: QPainter, rect: QRectF) -> None:
        """Draw line graph preview."""
        import math

        # Background
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Graph area
        margin = 8
        graph_rect = rect.adjusted(margin, margin, -margin, -margin * 2)

        # Draw grid
        painter.setPen(QPen(QColor(50, 50, 60), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = graph_rect.top() + graph_rect.height() * i / 4
            painter.drawLine(QPointF(graph_rect.left(), y), QPointF(graph_rect.right(), y))

        # Generate sample wave data
        line_color = QColor(79, 195, 247)
        points = []
        num_points = 30
        for i in range(num_points):
            x = graph_rect.left() + graph_rect.width() * i / (num_points - 1)
            # Simulate varying RPM over time
            t = i / num_points * 4 * math.pi
            value = 0.5 + 0.3 * math.sin(t) + 0.1 * math.sin(t * 3)
            y = graph_rect.bottom() - graph_rect.height() * value
            points.append(QPointF(x, y))

        # Draw filled area
        fill_color = QColor(79, 195, 247, 60)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        fill_points = points.copy()
        fill_points.append(QPointF(graph_rect.right(), graph_rect.bottom()))
        fill_points.append(QPointF(graph_rect.left(), graph_rect.bottom()))
        from PyQt6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(fill_points))

        # Draw line
        painter.setPen(QPen(line_color, 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Label
        painter.setPen(QPen(QColor(150, 150, 150)))
        font = painter.font()
        font.setPointSize(max(8, int(rect.height() * 0.1)))
        painter.setFont(font)
        label = self._config.properties.get("label", "RPM")
        painter.drawText(QRectF(rect.left(), rect.bottom() - 15, rect.width(), 15),
                        Qt.AlignmentFlag.AlignCenter, label)

    def _draw_bar_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Draw bar chart preview."""
        # Background
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Chart area
        margin = 8
        chart_rect = rect.adjusted(margin, margin, -margin, -margin * 2)

        # Sample data
        values = [0.7, 0.4, 0.9, 0.5, 0.8]
        colors = [QColor(76, 175, 80), QColor(33, 150, 243), QColor(255, 152, 0),
                  QColor(233, 30, 99), QColor(156, 39, 176)]

        bar_count = len(values)
        bar_spacing = 4
        bar_width = (chart_rect.width() - bar_spacing * (bar_count - 1)) / bar_count

        for i, value in enumerate(values):
            x = chart_rect.left() + i * (bar_width + bar_spacing)
            bar_height = chart_rect.height() * value
            bar_rect = QRectF(x, chart_rect.bottom() - bar_height, bar_width, bar_height)

            painter.setBrush(QBrush(colors[i % len(colors)]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bar_rect, 2, 2)

    def _draw_histogram(self, painter: QPainter, rect: QRectF) -> None:
        """Draw histogram preview."""
        import math
        import random

        # Background
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Chart area
        margin = 8
        chart_rect = rect.adjusted(margin, margin, -margin, -margin * 2)

        # Generate bell curve-like distribution
        bin_count = 15
        bins = []
        for i in range(bin_count):
            # Normal distribution approximation
            x = (i - bin_count / 2) / (bin_count / 4)
            value = math.exp(-x * x / 2) * 0.9 + 0.1
            bins.append(value)

        bar_width = chart_rect.width() / bin_count
        bar_color = QColor(255, 152, 0)

        for i, value in enumerate(bins):
            x = chart_rect.left() + i * bar_width
            bar_height = chart_rect.height() * value
            bar_rect = QRectF(x, chart_rect.bottom() - bar_height, bar_width - 1, bar_height)

            painter.setBrush(QBrush(bar_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(bar_rect)

        # Stats text
        painter.setPen(QPen(QColor(150, 150, 150)))
        font = painter.font()
        font.setPointSize(max(7, int(rect.height() * 0.08)))
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.bottom() - 12, rect.width(), 12),
                        Qt.AlignmentFlag.AlignCenter, "μ=5400 σ=820")

    def _draw_pie_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Draw pie chart preview."""
        center = rect.center()
        radius = min(rect.width(), rect.height()) * 0.4

        # Sample data
        values = [35, 25, 20, 15, 5]
        colors = [QColor(76, 175, 80), QColor(33, 150, 243), QColor(255, 152, 0),
                  QColor(233, 30, 99), QColor(156, 39, 176)]

        total = sum(values)
        start_angle = 90 * 16  # Start from top

        pie_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        for i, value in enumerate(values):
            span_angle = int(-360 * 16 * value / total)

            painter.setBrush(QBrush(colors[i % len(colors)]))
            painter.setPen(QPen(QColor(25, 25, 30), 2))
            painter.drawPie(pie_rect, start_angle, span_angle)

            start_angle += span_angle

        # Donut hole if enabled
        if self._config.properties.get("donut_mode", False):
            inner_radius = radius * self._config.properties.get("donut_ratio", 0.5)
            painter.setBrush(QBrush(QColor(25, 25, 30)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, inner_radius, inner_radius)

    def _draw_resize_handles(self, painter: QPainter) -> None:
        """Draw resize handles at corners."""
        rect = self.rect()
        handle_size = self.HANDLE_SIZE
        half = handle_size / 2

        painter.setBrush(QBrush(QColor(0, 120, 215)))
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        # Corner handles
        handles = [
            QRectF(rect.left() - half, rect.top() - half, handle_size, handle_size),
            QRectF(rect.right() - half, rect.top() - half, handle_size, handle_size),
            QRectF(rect.left() - half, rect.bottom() - half, handle_size, handle_size),
            QRectF(rect.right() - half, rect.bottom() - half, handle_size, handle_size),
        ]

        for handle in handles:
            painter.drawRect(handle)

    def itemChange(self, change, value):
        """Handle item changes (position, selection)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update config with new position
            pos = value
            self._config.x = int(pos.x())
            self._config.y = int(pos.y())

        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._is_selected = value
            self.update()

        return super().itemChange(change, value)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for resize detection."""
        self._resize_handle = self._get_resize_handle(event.pos())
        self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for resizing."""
        if self._resize_handle is not None and self._drag_start is not None:
            delta = event.pos() - self._drag_start
            self._resize(self._resize_handle, delta)
            self._drag_start = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        self._resize_handle = None
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def _get_resize_handle(self, pos: QPointF) -> Optional[int]:
        """Check if position is on a resize handle. Returns handle index or None."""
        if not self.isSelected():
            return None

        rect = self.rect()
        handle_size = self.HANDLE_SIZE * 2  # Larger hit area

        handles = [
            QRectF(rect.left() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size),
            QRectF(rect.right() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size),
            QRectF(rect.left() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size),
            QRectF(rect.right() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size),
        ]

        for i, handle in enumerate(handles):
            if handle.contains(pos):
                return i
        return None

    def _resize(self, handle: int, delta: QPointF) -> None:
        """Resize the widget based on handle dragged."""
        rect = self.rect()
        pos = self.pos()

        if handle == 0:  # Top-left
            new_w = max(self.MIN_SIZE, rect.width() - delta.x())
            new_h = max(self.MIN_SIZE, rect.height() - delta.y())
            self.setRect(0, 0, new_w, new_h)
            self.setPos(pos.x() + rect.width() - new_w, pos.y() + rect.height() - new_h)

        elif handle == 1:  # Top-right
            new_w = max(self.MIN_SIZE, rect.width() + delta.x())
            new_h = max(self.MIN_SIZE, rect.height() - delta.y())
            self.setRect(0, 0, new_w, new_h)
            self.setPos(pos.x(), pos.y() + rect.height() - new_h)

        elif handle == 2:  # Bottom-left
            new_w = max(self.MIN_SIZE, rect.width() - delta.x())
            new_h = max(self.MIN_SIZE, rect.height() + delta.y())
            self.setRect(0, 0, new_w, new_h)
            self.setPos(pos.x() + rect.width() - new_w, pos.y())

        elif handle == 3:  # Bottom-right
            new_w = max(self.MIN_SIZE, rect.width() + delta.x())
            new_h = max(self.MIN_SIZE, rect.height() + delta.y())
            self.setRect(0, 0, new_w, new_h)

        # Update config
        self._config.width = int(self.rect().width())
        self._config.height = int(self.rect().height())
        self._config.x = int(self.pos().x())
        self._config.y = int(self.pos().y())

    def sync_from_config(self) -> None:
        """Sync item position/size from config."""
        self.setRect(0, 0, self._config.width, self._config.height)
        self.setPos(self._config.x, self._config.y)
        self.setZValue(self._config.z_index)
        self.update()

    def set_preview_mode(self, enabled: bool) -> None:
        """Enable/disable preview mode."""
        self._preview_mode = enabled
        # Disable interaction in preview mode
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not enabled)
        self.update()

    def update_preview_data(self, data: Dict[int, float]) -> None:
        """Update preview values from simulator."""
        self._preview_values = data
        self.update()

    def _get_preview_value(self, channel_id: int, default: float = 0.0) -> float:
        """Get preview value for a channel."""
        if self._preview_mode and channel_id in self._preview_values:
            return self._preview_values[channel_id]
        return default


class ScreenCanvas(QGraphicsView):
    """
    Main canvas view for screen editing.
    Supports zoom, pan, drag-drop, and widget manipulation.
    """

    # Signals
    widget_selected = pyqtSignal(object)  # WidgetConfig or None
    widget_added = pyqtSignal(object)  # WidgetConfig
    widget_removed = pyqtSignal(str)  # widget_id
    widget_changed = pyqtSignal(object)  # WidgetConfig
    selection_changed = pyqtSignal(list)  # List of widget_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._screen_layout: Optional[ScreenLayout] = None
        self._grid_overlay: Optional[GridOverlay] = None
        self._widget_items: Dict[str, WidgetItem] = {}
        self._zoom_level = 1.0
        self._panning = False
        self._pan_start = QPointF()
        self._snap_to_grid = True
        self._preview_mode = False

        self._setup_view()

    def _setup_view(self) -> None:
        """Configure view settings."""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Background
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        # Accept drops
        self.setAcceptDrops(True)

    def set_screen_layout(self, layout: ScreenLayout) -> None:
        """Set the screen layout to edit."""
        self._screen_layout = layout
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        """Rebuild the scene from the screen layout."""
        self._scene.clear()
        self._widget_items.clear()

        if not self._screen_layout:
            return

        # Set scene size
        self._scene.setSceneRect(0, 0, self._screen_layout.width, self._screen_layout.height)

        # Add grid overlay
        self._grid_overlay = GridOverlay(
            self._screen_layout.width,
            self._screen_layout.height,
            self._screen_layout.grid_columns,
            self._screen_layout.grid_rows
        )
        self._scene.addItem(self._grid_overlay)
        self._grid_overlay.set_grid_visible(self._screen_layout.grid_visible)

        # Add background rect
        bg = QGraphicsRectItem(0, 0, self._screen_layout.width, self._screen_layout.height)
        bg.setBrush(QBrush(QColor(self._screen_layout.background_color)))
        bg.setPen(QPen(Qt.PenStyle.NoPen))
        bg.setZValue(-999)
        self._scene.addItem(bg)

        # Add widgets
        for widget_config in self._screen_layout.widgets:
            self._add_widget_item(widget_config)

        # Fit in view
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _add_widget_item(self, widget_config: WidgetConfig) -> WidgetItem:
        """Add a widget item to the scene."""
        item = WidgetItem(widget_config)
        self._scene.addItem(item)
        self._widget_items[widget_config.id] = item
        return item

    def add_widget(self, widget_type: WidgetType, x: int = 100, y: int = 100) -> Optional[WidgetConfig]:
        """Add a new widget to the screen."""
        if not self._screen_layout:
            return None

        definition = get_widget_definition(widget_type)
        if not definition:
            return None

        # Snap to grid if enabled
        if self._snap_to_grid:
            x, y = self._screen_layout.snap_to_grid_position(x, y)

        config = WidgetConfig(
            widget_type=widget_type,
            x=x,
            y=y,
            width=definition.default_width,
            height=definition.default_height,
        )

        self._screen_layout.add_widget(config)
        self._add_widget_item(config)
        self.widget_added.emit(config)

        return config

    def remove_selected_widgets(self) -> None:
        """Remove all selected widgets."""
        for item in self._scene.selectedItems():
            if isinstance(item, WidgetItem):
                widget_id = item.widget_id
                self._scene.removeItem(item)
                del self._widget_items[widget_id]
                if self._screen_layout:
                    self._screen_layout.remove_widget(widget_id)
                self.widget_removed.emit(widget_id)

    def get_selected_widget(self) -> Optional[WidgetConfig]:
        """Get the currently selected widget config."""
        selected = self._scene.selectedItems()
        for item in selected:
            if isinstance(item, WidgetItem):
                return item.config
        return None

    def get_selected_widgets(self) -> List[WidgetConfig]:
        """Get all selected widget configs."""
        widgets = []
        for item in self._scene.selectedItems():
            if isinstance(item, WidgetItem):
                widgets.append(item.config)
        return widgets

    def select_widget(self, widget_id: str) -> None:
        """Select a widget by ID."""
        self._scene.clearSelection()
        if widget_id in self._widget_items:
            self._widget_items[widget_id].setSelected(True)

    def set_grid_visible(self, visible: bool) -> None:
        """Show/hide the grid overlay."""
        if self._grid_overlay:
            self._grid_overlay.set_grid_visible(visible)
        if self._screen_layout:
            self._screen_layout.grid_visible = visible

    def set_snap_to_grid(self, enabled: bool) -> None:
        """Enable/disable snap to grid."""
        self._snap_to_grid = enabled
        if self._screen_layout:
            self._screen_layout.snap_to_grid = enabled

    def zoom_in(self) -> None:
        """Zoom in."""
        self._zoom_level = min(4.0, self._zoom_level * 1.2)
        self.setTransform(QTransform().scale(self._zoom_level, self._zoom_level))

    def zoom_out(self) -> None:
        """Zoom out."""
        self._zoom_level = max(0.25, self._zoom_level / 1.2)
        self.setTransform(QTransform().scale(self._zoom_level, self._zoom_level))

    def zoom_fit(self) -> None:
        """Fit screen in view."""
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = self.transform().m11()

    def zoom_100(self) -> None:
        """Reset to 100% zoom."""
        self._zoom_level = 1.0
        self.setTransform(QTransform())

    def set_preview_mode(self, enabled: bool) -> None:
        """Enable/disable preview mode for all widgets."""
        self._preview_mode = enabled
        for item in self._widget_items.values():
            item.set_preview_mode(enabled)
        # Hide grid in preview mode
        if self._grid_overlay:
            self._grid_overlay.set_grid_visible(not enabled)

    def update_preview_data(self, data: Dict[int, float]) -> None:
        """Update all widgets with preview data."""
        if not self._preview_mode:
            return
        for item in self._widget_items.values():
            item.update_preview_data(data)

    # Event handlers

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.remove_selected_widgets()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self._scene.clearSelection()
            event.accept()
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy_selected()
                event.accept()
            elif event.key() == Qt.Key.Key_X:
                self.cut_selected()
                event.accept()
            elif event.key() == Qt.Key.Key_V:
                self.paste()
                event.accept()
            elif event.key() == Qt.Key.Key_A:
                self.select_all()
                event.accept()
            elif event.key() == Qt.Key.Key_D:
                self._duplicate_selected()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for panning."""
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            # Emit selection change
            selected = [item.widget_id for item in self._scene.selectedItems()
                       if isinstance(item, WidgetItem)]
            self.selection_changed.emit(selected)

            widget = self.get_selected_widget()
            self.widget_selected.emit(widget)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show context menu."""
        menu = QMenu(self)

        selected = self.get_selected_widgets()

        if selected:
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.remove_selected_widgets)

            menu.addSeparator()

            duplicate_action = menu.addAction("Duplicate")
            duplicate_action.triggered.connect(self._duplicate_selected)

            menu.addSeparator()

            bring_front_action = menu.addAction("Bring to Front")
            bring_front_action.triggered.connect(self._bring_to_front)

            send_back_action = menu.addAction("Send to Back")
            send_back_action.triggered.connect(self._send_to_back)

        else:
            # Add widget submenu
            add_menu = menu.addMenu("Add Widget")
            for widget_type in WidgetType:
                action = add_menu.addAction(widget_type.value.replace("_", " ").title())
                action.setData(widget_type)
                action.triggered.connect(lambda checked, wt=widget_type: self._add_widget_at_cursor(wt, event.pos()))

        menu.exec(event.globalPos())

    def _add_widget_at_cursor(self, widget_type: WidgetType, pos) -> None:
        """Add widget at cursor position."""
        scene_pos = self.mapToScene(pos)
        self.add_widget(widget_type, int(scene_pos.x()), int(scene_pos.y()))

    def _duplicate_selected(self) -> None:
        """Duplicate selected widgets."""
        if not self._screen_layout:
            return

        for widget in self.get_selected_widgets():
            new_config = self._screen_layout.duplicate_widget(widget.id)
            if new_config:
                self._add_widget_item(new_config)

    def _bring_to_front(self) -> None:
        """Bring selected widgets to front."""
        if not self._screen_layout:
            return

        for widget in self.get_selected_widgets():
            self._screen_layout.bring_to_front(widget.id)
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()

    def _send_to_back(self) -> None:
        """Send selected widgets to back."""
        if not self._screen_layout:
            return

        for widget in self.get_selected_widgets():
            self._screen_layout.send_to_back(widget.id)
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()

    # Alignment methods

    def align_left(self) -> None:
        """Align selected widgets to left edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        left = min(w.x for w in widgets)
        for widget in widgets:
            widget.x = left
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def align_center_h(self) -> None:
        """Align selected widgets to horizontal center."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        # Find center of all widgets
        centers = [(w.x + w.width / 2) for w in widgets]
        center = sum(centers) / len(centers)

        for widget in widgets:
            widget.x = int(center - widget.width / 2)
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def align_right(self) -> None:
        """Align selected widgets to right edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        right = max(w.x + w.width for w in widgets)
        for widget in widgets:
            widget.x = right - widget.width
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def align_top(self) -> None:
        """Align selected widgets to top edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        top = min(w.y for w in widgets)
        for widget in widgets:
            widget.y = top
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def align_center_v(self) -> None:
        """Align selected widgets to vertical center."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        centers = [(w.y + w.height / 2) for w in widgets]
        center = sum(centers) / len(centers)

        for widget in widgets:
            widget.y = int(center - widget.height / 2)
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def align_bottom(self) -> None:
        """Align selected widgets to bottom edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        bottom = max(w.y + w.height for w in widgets)
        for widget in widgets:
            widget.y = bottom - widget.height
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def distribute_horizontal(self) -> None:
        """Distribute selected widgets evenly horizontally."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 3:
            return

        # Sort by x position
        sorted_widgets = sorted(widgets, key=lambda w: w.x)

        # Calculate total space and gaps
        left = sorted_widgets[0].x
        right = sorted_widgets[-1].x + sorted_widgets[-1].width
        total_width = sum(w.width for w in sorted_widgets)
        available_space = right - left - total_width
        gap = available_space / (len(sorted_widgets) - 1)

        # Distribute
        current_x = left
        for widget in sorted_widgets:
            widget.x = int(current_x)
            current_x += widget.width + gap
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def distribute_vertical(self) -> None:
        """Distribute selected widgets evenly vertically."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 3:
            return

        # Sort by y position
        sorted_widgets = sorted(widgets, key=lambda w: w.y)

        # Calculate total space and gaps
        top = sorted_widgets[0].y
        bottom = sorted_widgets[-1].y + sorted_widgets[-1].height
        total_height = sum(w.height for w in sorted_widgets)
        available_space = bottom - top - total_height
        gap = available_space / (len(sorted_widgets) - 1)

        # Distribute
        current_y = top
        for widget in sorted_widgets:
            widget.y = int(current_y)
            current_y += widget.height + gap
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def match_width(self) -> None:
        """Match width of selected widgets to first selected."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        target_width = widgets[0].width
        for widget in widgets[1:]:
            widget.width = target_width
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def match_height(self) -> None:
        """Match height of selected widgets to first selected."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        target_height = widgets[0].height
        for widget in widgets[1:]:
            widget.height = target_height
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    def match_size(self) -> None:
        """Match size of selected widgets to first selected."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return

        target_width = widgets[0].width
        target_height = widgets[0].height
        for widget in widgets[1:]:
            widget.width = target_width
            widget.height = target_height
            if widget.id in self._widget_items:
                self._widget_items[widget.id].sync_from_config()
        self.widget_changed.emit(widgets[0])

    # Copy/Paste methods

    def copy_selected(self) -> None:
        """Copy selected widgets to clipboard."""
        widgets = self.get_selected_widgets()
        if not widgets:
            return

        # Serialize widgets to JSON
        widget_data = []
        for widget in widgets:
            data = {
                "widget_type": widget.widget_type.value,
                "x": widget.x,
                "y": widget.y,
                "width": widget.width,
                "height": widget.height,
                "name": widget.name,
                "properties": widget.properties.copy(),
                "channel_bindings": widget.channel_bindings.copy(),
            }
            widget_data.append(data)

        # Copy to clipboard as JSON
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        mime_data.setText(json.dumps({"widgets": widget_data}))
        mime_data.setData("application/x-racing-dashboard-widgets",
                          json.dumps(widget_data).encode())
        clipboard.setMimeData(mime_data)
        logger.debug(f"Copied {len(widgets)} widget(s) to clipboard")

    def cut_selected(self) -> None:
        """Cut selected widgets (copy + delete)."""
        self.copy_selected()
        self.remove_selected_widgets()

    def paste(self) -> None:
        """Paste widgets from clipboard."""
        if not self._screen_layout:
            return

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        widget_data = None

        # Try our custom format first
        if mime_data.hasFormat("application/x-racing-dashboard-widgets"):
            data = mime_data.data("application/x-racing-dashboard-widgets").data()
            widget_data = json.loads(data.decode())
        elif mime_data.hasText():
            try:
                parsed = json.loads(mime_data.text())
                if "widgets" in parsed:
                    widget_data = parsed["widgets"]
            except (json.JSONDecodeError, KeyError):
                pass

        if not widget_data:
            return

        # Clear current selection
        self._scene.clearSelection()

        # Offset for pasted widgets
        offset = 20

        # Create new widgets
        new_items = []
        for data in widget_data:
            try:
                widget_type = WidgetType(data["widget_type"])
                config = WidgetConfig(
                    widget_type=widget_type,
                    x=data["x"] + offset,
                    y=data["y"] + offset,
                    width=data["width"],
                    height=data["height"],
                    name=data.get("name", ""),
                    properties=data.get("properties", {}),
                    channel_bindings=data.get("channel_bindings", {}),
                )

                self._screen_layout.add_widget(config)
                item = self._add_widget_item(config)
                item.setSelected(True)
                new_items.append(item)
                self.widget_added.emit(config)

            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to paste widget: {e}")

        logger.debug(f"Pasted {len(new_items)} widget(s)")

    def select_all(self) -> None:
        """Select all widgets."""
        for item in self._widget_items.values():
            item.setSelected(True)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Handle drop."""
        if event.mimeData().hasText():
            widget_type_str = event.mimeData().text()
            try:
                widget_type = WidgetType(widget_type_str)
                pos = self.mapToScene(event.position().toPoint())
                self.add_widget(widget_type, int(pos.x()), int(pos.y()))
                event.acceptProposedAction()
            except ValueError:
                pass
