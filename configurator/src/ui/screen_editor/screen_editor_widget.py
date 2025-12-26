# Screen Editor Widget
"""Main screen editor widget combining canvas, palette, and property panel."""

import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QLabel, QComboBox, QPushButton, QFrame, QToolButton, QMenu,
    QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon

from ui.screen_editor.canvas import ScreenCanvas
from ui.screen_editor.widget_palette import WidgetPalette, CompactWidgetPalette
from ui.screen_editor.property_panel import PropertyPanel
from ui.screen_editor.preview_simulator import DataSimulator, SimulationMode
from models.screen_layout import ScreenLayout, WidgetConfig, create_default_screen
from models.widget_types import WidgetType, WidgetDefinition

logger = logging.getLogger(__name__)


class ScreenEditorWidget(QWidget):
    """
    Complete screen editor with toolbar, canvas, palette, and properties.

    Layout:
    ┌────────────────────────────────────────────────────────┐
    │ Toolbar: Screen selector | Zoom | Grid | Add widgets   │
    ├──────────┬──────────────────────────────┬──────────────┤
    │          │                              │              │
    │  Widget  │         Canvas               │  Property    │
    │  Palette │       (1024x600)             │  Panel       │
    │          │                              │              │
    └──────────┴──────────────────────────────┴──────────────┘
    """

    screen_changed = pyqtSignal()  # Emitted when screen layout changes
    widget_selected = pyqtSignal(object)  # WidgetConfig or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._screens: List[ScreenLayout] = []
        self._current_screen_index = 0

        # Preview simulator
        self._simulator = DataSimulator(self)
        self._preview_mode = False

        self._setup_ui()
        self._connect_signals()
        self._simulator.data_updated.connect(self._on_simulator_data)

    def _setup_ui(self) -> None:
        """Setup the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create canvas first (needed by toolbar)
        self._canvas = ScreenCanvas()

        # Widget Palette (left)
        self._palette = WidgetPalette()
        self._palette.setMinimumWidth(150)
        self._palette.setMaximumWidth(250)

        # Property Panel (right)
        self._properties = PropertyPanel()
        self._properties.setMinimumWidth(200)
        self._properties.setMaximumWidth(350)

        # Toolbar (now canvas exists)
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        # Main content splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)

        self._splitter.addWidget(self._palette)
        self._splitter.addWidget(self._canvas)
        self._splitter.addWidget(self._properties)

        # Set splitter sizes
        self._splitter.setSizes([200, 800, 280])

        layout.addWidget(self._splitter)

        # Status bar
        self._status = self._create_status_bar()
        layout.addWidget(self._status)

    def _create_toolbar(self) -> QToolBar:
        """Create the editor toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #444;
                padding: 4px;
                spacing: 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px 8px;
                color: #ddd;
            }
            QToolButton:hover {
                background-color: #3d3d3d;
                border-color: #555;
            }
            QToolButton:pressed {
                background-color: #2d2d2d;
            }
            QToolButton:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """)

        # Screen selector
        toolbar.addWidget(QLabel("Screen:"))

        self._screen_combo = QComboBox()
        self._screen_combo.setMinimumWidth(150)
        self._screen_combo.currentIndexChanged.connect(self._on_screen_selected)
        toolbar.addWidget(self._screen_combo)

        # Add/Remove screen buttons
        self._add_screen_btn = QToolButton()
        self._add_screen_btn.setText("+")
        self._add_screen_btn.setToolTip("Add new screen")
        self._add_screen_btn.clicked.connect(self._add_screen)
        toolbar.addWidget(self._add_screen_btn)

        self._remove_screen_btn = QToolButton()
        self._remove_screen_btn.setText("-")
        self._remove_screen_btn.setToolTip("Remove current screen")
        self._remove_screen_btn.clicked.connect(self._remove_screen)
        toolbar.addWidget(self._remove_screen_btn)

        toolbar.addSeparator()

        # Zoom controls
        self._zoom_out_btn = QToolButton()
        self._zoom_out_btn.setText("-")
        self._zoom_out_btn.setToolTip("Zoom Out")
        self._zoom_out_btn.clicked.connect(self._canvas.zoom_out)
        toolbar.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(50)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self._zoom_label)

        self._zoom_in_btn = QToolButton()
        self._zoom_in_btn.setText("+")
        self._zoom_in_btn.setToolTip("Zoom In")
        self._zoom_in_btn.clicked.connect(self._canvas.zoom_in)
        toolbar.addWidget(self._zoom_in_btn)

        self._zoom_fit_btn = QToolButton()
        self._zoom_fit_btn.setText("Fit")
        self._zoom_fit_btn.setToolTip("Fit to View")
        self._zoom_fit_btn.clicked.connect(self._canvas.zoom_fit)
        toolbar.addWidget(self._zoom_fit_btn)

        self._zoom_100_btn = QToolButton()
        self._zoom_100_btn.setText("1:1")
        self._zoom_100_btn.setToolTip("Reset to 100% (1:1)")
        self._zoom_100_btn.clicked.connect(self._canvas.zoom_100)
        toolbar.addWidget(self._zoom_100_btn)

        toolbar.addSeparator()

        # Grid controls
        self._grid_btn = QToolButton()
        self._grid_btn.setText("Grid")
        self._grid_btn.setCheckable(True)
        self._grid_btn.setChecked(True)
        self._grid_btn.setToolTip("Show/Hide Grid")
        self._grid_btn.toggled.connect(self._canvas.set_grid_visible)
        toolbar.addWidget(self._grid_btn)

        self._snap_btn = QToolButton()
        self._snap_btn.setText("Snap")
        self._snap_btn.setCheckable(True)
        self._snap_btn.setChecked(True)
        self._snap_btn.setToolTip("Snap to Grid")
        self._snap_btn.toggled.connect(self._canvas.set_snap_to_grid)
        toolbar.addWidget(self._snap_btn)

        toolbar.addSeparator()

        # Quick add widget menu
        self._add_widget_btn = QToolButton()
        self._add_widget_btn.setText("Add Widget")
        self._add_widget_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._add_widget_menu = QMenu()

        for widget_type in WidgetType:
            action = self._add_widget_menu.addAction(
                widget_type.value.replace("_", " ").title()
            )
            action.triggered.connect(
                lambda checked, wt=widget_type: self._add_widget(wt)
            )

        self._add_widget_btn.setMenu(self._add_widget_menu)
        toolbar.addWidget(self._add_widget_btn)

        toolbar.addSeparator()

        # Align button with dropdown menu
        self._align_btn = QToolButton()
        self._align_btn.setText("Align")
        self._align_btn.setToolTip("Alignment and Layout Tools")
        self._align_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._align_menu = QMenu()

        # Alignment actions
        align_left = self._align_menu.addAction("Align Left")
        align_left.triggered.connect(self._canvas.align_left)
        align_center_h = self._align_menu.addAction("Align Center (H)")
        align_center_h.triggered.connect(self._canvas.align_center_h)
        align_right = self._align_menu.addAction("Align Right")
        align_right.triggered.connect(self._canvas.align_right)

        self._align_menu.addSeparator()

        align_top = self._align_menu.addAction("Align Top")
        align_top.triggered.connect(self._canvas.align_top)
        align_center_v = self._align_menu.addAction("Align Center (V)")
        align_center_v.triggered.connect(self._canvas.align_center_v)
        align_bottom = self._align_menu.addAction("Align Bottom")
        align_bottom.triggered.connect(self._canvas.align_bottom)

        self._align_menu.addSeparator()

        dist_h = self._align_menu.addAction("Distribute Horizontal")
        dist_h.triggered.connect(self._canvas.distribute_horizontal)
        dist_v = self._align_menu.addAction("Distribute Vertical")
        dist_v.triggered.connect(self._canvas.distribute_vertical)

        self._align_menu.addSeparator()

        match_w = self._align_menu.addAction("Match Width")
        match_w.triggered.connect(self._canvas.match_width)
        match_h = self._align_menu.addAction("Match Height")
        match_h.triggered.connect(self._canvas.match_height)
        match_s = self._align_menu.addAction("Match Size")
        match_s.triggered.connect(self._canvas.match_size)

        self._align_btn.setMenu(self._align_menu)
        toolbar.addWidget(self._align_btn)

        # Edit button with copy/paste
        self._edit_btn = QToolButton()
        self._edit_btn.setText("Edit")
        self._edit_btn.setToolTip("Edit Operations")
        self._edit_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._edit_menu = QMenu()

        copy_action = self._edit_menu.addAction("Copy (Ctrl+C)")
        copy_action.triggered.connect(self._canvas.copy_selected)
        cut_action = self._edit_menu.addAction("Cut (Ctrl+X)")
        cut_action.triggered.connect(self._canvas.cut_selected)
        paste_action = self._edit_menu.addAction("Paste (Ctrl+V)")
        paste_action.triggered.connect(self._canvas.paste)

        self._edit_menu.addSeparator()

        duplicate_action = self._edit_menu.addAction("Duplicate (Ctrl+D)")
        duplicate_action.triggered.connect(self._canvas._duplicate_selected)

        self._edit_menu.addSeparator()

        select_all_action = self._edit_menu.addAction("Select All (Ctrl+A)")
        select_all_action.triggered.connect(self._canvas.select_all)

        self._edit_btn.setMenu(self._edit_menu)
        toolbar.addWidget(self._edit_btn)

        toolbar.addSeparator()

        # Preview controls
        toolbar.addWidget(QLabel("Preview:"))

        self._preview_btn = QToolButton()
        self._preview_btn.setText("▶ Play")
        self._preview_btn.setToolTip("Start/Stop Preview Simulation")
        self._preview_btn.setCheckable(True)
        self._preview_btn.setStyleSheet("""
            QToolButton:checked {
                background-color: #228B22;
                border-color: #228B22;
            }
        """)
        self._preview_btn.toggled.connect(self._toggle_preview)
        toolbar.addWidget(self._preview_btn)

        self._preview_mode_combo = QComboBox()
        self._preview_mode_combo.setMinimumWidth(120)
        self._preview_mode_combo.addItem("Idle", SimulationMode.IDLE)
        self._preview_mode_combo.addItem("Street", SimulationMode.STREET)
        self._preview_mode_combo.addItem("Track Warmup", SimulationMode.TRACK_WARMUP)
        self._preview_mode_combo.addItem("Track Hotlap", SimulationMode.TRACK_HOTLAP)
        self._preview_mode_combo.addItem("Drag Launch", SimulationMode.DRAG_LAUNCH)
        self._preview_mode_combo.setCurrentIndex(3)  # Default to hotlap
        self._preview_mode_combo.currentIndexChanged.connect(self._on_preview_mode_changed)
        toolbar.addWidget(self._preview_mode_combo)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Delete button
        self._delete_btn = QToolButton()
        self._delete_btn.setText("Delete")
        self._delete_btn.setToolTip("Delete Selected (Del)")
        self._delete_btn.clicked.connect(self._canvas.remove_selected_widgets)
        toolbar.addWidget(self._delete_btn)

        return toolbar

    def _create_status_bar(self) -> QFrame:
        """Create status bar."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-top: 1px solid #444;
            }
            QLabel {
                color: #888;
                padding: 4px 8px;
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._size_label = QLabel("1024 x 600")
        layout.addWidget(self._size_label)

        self._widget_count_label = QLabel("0 widgets")
        layout.addWidget(self._widget_count_label)

        self._selection_label = QLabel("No selection")
        layout.addWidget(self._selection_label)

        layout.addStretch()

        self._hint_label = QLabel("Drag widgets from palette or right-click to add")
        layout.addWidget(self._hint_label)

        return frame

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Canvas signals
        self._canvas.widget_selected.connect(self._on_widget_selected)
        self._canvas.widget_added.connect(self._on_widget_added)
        self._canvas.widget_removed.connect(self._on_widget_removed)
        self._canvas.selection_changed.connect(self._on_selection_changed)

        # Palette signals
        self._palette.widget_selected.connect(self._on_palette_widget_selected)

        # Property panel signals
        self._properties.widget_changed.connect(self._on_property_changed)

    def set_screens(self, screens: List[ScreenLayout]) -> None:
        """Set the list of screens to edit."""
        self._screens = screens
        self._update_screen_combo()

        if screens:
            self._select_screen(0)

    def get_screens(self) -> List[ScreenLayout]:
        """Get all screens."""
        return self._screens

    def get_current_screen(self) -> Optional[ScreenLayout]:
        """Get the currently active screen."""
        if 0 <= self._current_screen_index < len(self._screens):
            return self._screens[self._current_screen_index]
        return None

    def _update_screen_combo(self) -> None:
        """Update screen selector combo box."""
        self._screen_combo.blockSignals(True)
        self._screen_combo.clear()

        for i, screen in enumerate(self._screens):
            self._screen_combo.addItem(f"{i + 1}. {screen.name}")

        self._screen_combo.setCurrentIndex(self._current_screen_index)
        self._screen_combo.blockSignals(False)

        # Update remove button state
        self._remove_screen_btn.setEnabled(len(self._screens) > 1)

    def _select_screen(self, index: int) -> None:
        """Select a screen by index."""
        if 0 <= index < len(self._screens):
            self._current_screen_index = index
            screen = self._screens[index]
            self._canvas.set_screen_layout(screen)
            self._properties.set_widget(None)
            self._update_status()

    def _add_screen(self) -> None:
        """Add a new screen."""
        if len(self._screens) >= 10:
            QMessageBox.warning(self, "Maximum Screens", "Maximum of 10 screens allowed.")
            return

        name = f"Screen {len(self._screens) + 1}"
        screen = ScreenLayout(name=name)
        self._screens.append(screen)
        self._update_screen_combo()
        self._select_screen(len(self._screens) - 1)
        self._screen_combo.setCurrentIndex(self._current_screen_index)
        self.screen_changed.emit()

    def _remove_screen(self) -> None:
        """Remove current screen."""
        if len(self._screens) <= 1:
            return

        reply = QMessageBox.question(
            self, "Remove Screen",
            f"Remove '{self._screens[self._current_screen_index].name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self._screens[self._current_screen_index]
            if self._current_screen_index >= len(self._screens):
                self._current_screen_index = len(self._screens) - 1
            self._update_screen_combo()
            self._select_screen(self._current_screen_index)
            self.screen_changed.emit()

    def _add_widget(self, widget_type: WidgetType) -> None:
        """Add a widget to the current screen."""
        # Add at center of visible area
        screen = self.get_current_screen()
        if screen:
            x = screen.width // 2 - 50
            y = screen.height // 2 - 50
            self._canvas.add_widget(widget_type, x, y)

    def _update_status(self) -> None:
        """Update status bar."""
        screen = self.get_current_screen()
        if screen:
            self._size_label.setText(f"{screen.width} x {screen.height}")
            self._widget_count_label.setText(f"{len(screen.widgets)} widgets")
        else:
            self._size_label.setText("-")
            self._widget_count_label.setText("-")

    # Signal handlers

    def _on_screen_selected(self, index: int) -> None:
        """Handle screen selection from combo box."""
        if index >= 0:
            self._select_screen(index)

    def _on_widget_selected(self, widget_config: Optional[WidgetConfig]) -> None:
        """Handle widget selection on canvas."""
        self._properties.set_widget(widget_config)
        self.widget_selected.emit(widget_config)

        if widget_config:
            self._selection_label.setText(f"Selected: {widget_config.name}")
        else:
            self._selection_label.setText("No selection")

    def _on_widget_added(self, widget_config: WidgetConfig) -> None:
        """Handle widget added."""
        self._update_status()
        self.screen_changed.emit()
        logger.debug(f"Widget added: {widget_config.name}")

    def _on_widget_removed(self, widget_id: str) -> None:
        """Handle widget removed."""
        self._update_status()
        self._properties.set_widget(None)
        self.screen_changed.emit()
        logger.debug(f"Widget removed: {widget_id}")

    def _on_selection_changed(self, widget_ids: List[str]) -> None:
        """Handle selection change."""
        count = len(widget_ids)
        if count == 0:
            self._selection_label.setText("No selection")
        elif count == 1:
            widget = self._canvas.get_selected_widget()
            if widget:
                self._selection_label.setText(f"Selected: {widget.name}")
        else:
            self._selection_label.setText(f"{count} widgets selected")

    def _on_palette_widget_selected(self, definition: WidgetDefinition) -> None:
        """Handle widget selected from palette (click, not drag)."""
        self._add_widget(definition.widget_type)

    def _on_property_changed(self, widget_config: WidgetConfig) -> None:
        """Handle property changed in panel."""
        # Update canvas item
        if widget_config.id in self._canvas._widget_items:
            self._canvas._widget_items[widget_config.id].sync_from_config()
            self._canvas._widget_items[widget_config.id].update()

        self.screen_changed.emit()

    # Preview mode methods

    def _toggle_preview(self, checked: bool) -> None:
        """Toggle preview simulation on/off."""
        self._preview_mode = checked

        if checked:
            # Start simulation
            mode = self._preview_mode_combo.currentData()
            self._simulator.set_mode(mode)
            self._simulator.start()
            self._preview_btn.setText("■ Stop")
            self._hint_label.setText("Preview Mode - Live data simulation")
            self._canvas.set_preview_mode(True)
        else:
            # Stop simulation
            self._simulator.stop()
            self._preview_btn.setText("▶ Play")
            self._hint_label.setText("Drag widgets from palette or right-click to add")
            self._canvas.set_preview_mode(False)

    def _on_preview_mode_changed(self, index: int) -> None:
        """Handle preview mode selection change."""
        mode = self._preview_mode_combo.currentData()
        if mode and self._simulator.is_running():
            self._simulator.set_mode(mode)

    def _on_simulator_data(self, data: dict) -> None:
        """Handle simulated data from simulator."""
        if self._preview_mode:
            self._canvas.update_preview_data(data)
