# Screen Editor Canvas
"""Main canvas for visual screen editing using QGraphicsScene/QGraphicsView."""

import logging
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem,
    QMenu, QWidget, QVBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSizeF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QWheelEvent,
    QKeyEvent, QContextMenuEvent, QTransform
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

        # Grid lines
        pen = QPen(QColor(60, 60, 60), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        # Vertical lines
        for i in range(1, self._columns):
            x = i * cell_w
            painter.drawLine(QPointF(x, 0), QPointF(x, rect.height()))

        # Horizontal lines
        for i in range(1, self._rows):
            y = i * cell_h
            painter.drawLine(QPointF(0, y), QPointF(rect.width(), y))

        # Border
        pen = QPen(QColor(80, 80, 80), 2)
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

        # Background
        if self._config.widget_type == WidgetType.RPM_GAUGE:
            color = QColor(40, 80, 40)
        elif self._config.widget_type == WidgetType.SPEEDOMETER:
            color = QColor(40, 40, 80)
        elif self._config.widget_type == WidgetType.GEAR_INDICATOR:
            color = QColor(80, 60, 40)
        elif self._config.widget_type == WidgetType.SHIFT_LIGHTS:
            color = QColor(80, 40, 40)
        elif self._config.widget_type == WidgetType.TEMP_GAUGE:
            color = QColor(80, 50, 30)
        elif self._config.widget_type == WidgetType.G_FORCE_METER:
            color = QColor(50, 50, 80)
        elif self._config.widget_type == WidgetType.LAP_TIMER:
            color = QColor(60, 60, 60)
        else:
            color = QColor(50, 50, 50)

        painter.setBrush(QBrush(color))

        # Border
        if self.isSelected():
            pen = QPen(QColor(0, 120, 215), 2)
        else:
            pen = QPen(QColor(100, 100, 100), 1)
        painter.setPen(pen)

        painter.drawRoundedRect(rect, 4, 4)

        # Widget name
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        name = self._config.name or self._definition.display_name if self._definition else "Widget"
        painter.drawText(rect.adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, name)

        # Widget type icon/preview
        type_text = self._config.widget_type.value.replace("_", " ").title()
        painter.setPen(QPen(QColor(150, 150, 150)))
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, type_text)

        # Draw resize handles if selected
        if self.isSelected():
            self._draw_resize_handles(painter)

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
