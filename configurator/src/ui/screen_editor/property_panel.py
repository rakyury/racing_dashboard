# Property Panel
"""Property panel for editing widget properties."""

import logging
from typing import Optional, Any, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPushButton, QColorDialog,
    QFormLayout, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from models.widget_types import (
    WidgetType, WidgetProperty, WidgetDefinition,
    get_widget_definition
)
from models.screen_layout import WidgetConfig

logger = logging.getLogger(__name__)


class ColorButton(QPushButton):
    """Button for color selection."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#ffffff", parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setMinimumWidth(60)
        self.setMaximumWidth(100)

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str) -> None:
        self._color = value
        self._update_style()

    def _update_style(self) -> None:
        """Update button style to show current color."""
        text_color = "#fff" if self._is_dark_color(self._color) else "#000"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {text_color};
                border: 1px solid #666;
                border-radius: 3px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                border-color: #0078d4;
            }}
        """)
        self.setText(self._color)

    def _is_dark_color(self, hex_color: str) -> bool:
        """Check if color is dark for text contrast."""
        try:
            color = QColor(hex_color)
            luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
            return luminance < 128
        except:
            return False

    def _pick_color(self) -> None:
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)


class PropertyPanel(QWidget):
    """
    Panel for editing properties of selected widget(s).
    Dynamically generates property editors based on widget type.
    """

    property_changed = pyqtSignal(str, object)  # property_name, new_value
    widget_changed = pyqtSignal(object)  # WidgetConfig

    def __init__(self, parent=None):
        super().__init__(parent)
        self._widget_config: Optional[WidgetConfig] = None
        self._property_widgets: Dict[str, QWidget] = {}
        self._updating = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QLabel("Properties")
        self._header.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #fff;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(self._header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
        """)

        # Container for properties
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(8, 8, 8, 8)
        self._container_layout.setSpacing(8)

        # Placeholder
        self._placeholder = QLabel("Select a widget to edit properties")
        self._placeholder.setStyleSheet("color: #666;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._container_layout.addWidget(self._placeholder)
        self._container_layout.addStretch()

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

    def set_widget(self, widget_config: Optional[WidgetConfig]) -> None:
        """Set the widget to edit."""
        self._widget_config = widget_config
        self._rebuild_properties()

    def _rebuild_properties(self) -> None:
        """Rebuild property editors for current widget."""
        # Clear current widgets
        self._property_widgets.clear()
        while self._container_layout.count() > 0:
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._widget_config:
            # Show placeholder
            self._placeholder = QLabel("Select a widget to edit properties")
            self._placeholder.setStyleSheet("color: #666;")
            self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._container_layout.addWidget(self._placeholder)
            self._container_layout.addStretch()
            self._header.setText("Properties")
            return

        # Update header
        definition = get_widget_definition(self._widget_config.widget_type)
        name = definition.display_name if definition else "Widget"
        self._header.setText(f"Properties - {name}")

        # Position/Size group
        self._add_transform_group()

        # Widget-specific properties
        if definition:
            self._add_widget_properties(definition)

        self._container_layout.addStretch()

    def _add_transform_group(self) -> None:
        """Add position and size properties."""
        group = QGroupBox("Transform")
        group.setStyleSheet(self._group_style())
        form = QFormLayout(group)
        form.setSpacing(6)

        # Name
        name_edit = QLineEdit(self._widget_config.name)
        name_edit.textChanged.connect(lambda v: self._on_property_changed("name", v))
        self._property_widgets["name"] = name_edit
        form.addRow("Name:", name_edit)

        # Position
        pos_layout = QHBoxLayout()

        x_spin = QSpinBox()
        x_spin.setRange(0, 9999)
        x_spin.setValue(self._widget_config.x)
        x_spin.valueChanged.connect(lambda v: self._on_property_changed("x", v))
        self._property_widgets["x"] = x_spin
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(x_spin)

        y_spin = QSpinBox()
        y_spin.setRange(0, 9999)
        y_spin.setValue(self._widget_config.y)
        y_spin.valueChanged.connect(lambda v: self._on_property_changed("y", v))
        self._property_widgets["y"] = y_spin
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(y_spin)

        form.addRow("Position:", pos_layout)

        # Size
        size_layout = QHBoxLayout()

        w_spin = QSpinBox()
        w_spin.setRange(20, 9999)
        w_spin.setValue(self._widget_config.width)
        w_spin.valueChanged.connect(lambda v: self._on_property_changed("width", v))
        self._property_widgets["width"] = w_spin
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(w_spin)

        h_spin = QSpinBox()
        h_spin.setRange(20, 9999)
        h_spin.setValue(self._widget_config.height)
        h_spin.valueChanged.connect(lambda v: self._on_property_changed("height", v))
        self._property_widgets["height"] = h_spin
        size_layout.addWidget(QLabel("H:"))
        size_layout.addWidget(h_spin)

        form.addRow("Size:", size_layout)

        # Visibility
        visible_check = QCheckBox()
        visible_check.setChecked(self._widget_config.visible)
        visible_check.stateChanged.connect(lambda v: self._on_property_changed("visible", v == Qt.CheckState.Checked.value))
        self._property_widgets["visible"] = visible_check
        form.addRow("Visible:", visible_check)

        # Locked
        locked_check = QCheckBox()
        locked_check.setChecked(self._widget_config.locked)
        locked_check.stateChanged.connect(lambda v: self._on_property_changed("locked", v == Qt.CheckState.Checked.value))
        self._property_widgets["locked"] = locked_check
        form.addRow("Locked:", locked_check)

        self._container_layout.addWidget(group)

    def _add_widget_properties(self, definition: WidgetDefinition) -> None:
        """Add widget-specific properties."""
        if not definition.properties:
            return

        group = QGroupBox("Widget Settings")
        group.setStyleSheet(self._group_style())
        form = QFormLayout(group)
        form.setSpacing(6)

        for prop in definition.properties:
            editor = self._create_property_editor(prop)
            if editor:
                self._property_widgets[prop.name] = editor
                form.addRow(f"{prop.display_name}:", editor)

        self._container_layout.addWidget(group)

    def _create_property_editor(self, prop: WidgetProperty) -> Optional[QWidget]:
        """Create an editor widget for a property."""
        current_value = self._widget_config.properties.get(prop.name, prop.default_value)

        if prop.property_type == "int":
            spin = QSpinBox()
            spin.setRange(int(prop.min_value or 0), int(prop.max_value or 99999))
            spin.setValue(int(current_value))
            spin.valueChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return spin

        elif prop.property_type == "float":
            spin = QDoubleSpinBox()
            spin.setRange(prop.min_value or 0.0, prop.max_value or 99999.0)
            spin.setDecimals(2)
            spin.setValue(float(current_value))
            spin.valueChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return spin

        elif prop.property_type == "string":
            edit = QLineEdit(str(current_value))
            edit.textChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return edit

        elif prop.property_type == "bool":
            check = QCheckBox()
            check.setChecked(bool(current_value))
            check.stateChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v == Qt.CheckState.Checked.value))
            return check

        elif prop.property_type == "color":
            btn = ColorButton(str(current_value))
            btn.color_changed.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return btn

        elif prop.property_type == "enum":
            combo = QComboBox()
            if prop.enum_values:
                combo.addItems(prop.enum_values)
                if current_value in prop.enum_values:
                    combo.setCurrentText(str(current_value))
            combo.currentTextChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return combo

        elif prop.property_type == "data_source":
            # For now, simple text input for data source
            edit = QLineEdit(str(current_value))
            edit.setPlaceholderText("e.g., engine_rpm")
            edit.textChanged.connect(lambda v, n=prop.name: self._on_widget_property_changed(n, v))
            return edit

        return None

    def _on_property_changed(self, name: str, value: Any) -> None:
        """Handle transform property change."""
        if self._updating or not self._widget_config:
            return

        if hasattr(self._widget_config, name):
            setattr(self._widget_config, name, value)
            self.property_changed.emit(name, value)
            self.widget_changed.emit(self._widget_config)

    def _on_widget_property_changed(self, name: str, value: Any) -> None:
        """Handle widget-specific property change."""
        if self._updating or not self._widget_config:
            return

        self._widget_config.properties[name] = value
        self.property_changed.emit(name, value)
        self.widget_changed.emit(self._widget_config)

    def update_from_widget(self) -> None:
        """Update property values from current widget config."""
        if not self._widget_config:
            return

        self._updating = True
        try:
            # Update transform properties
            if "name" in self._property_widgets:
                self._property_widgets["name"].setText(self._widget_config.name)
            if "x" in self._property_widgets:
                self._property_widgets["x"].setValue(self._widget_config.x)
            if "y" in self._property_widgets:
                self._property_widgets["y"].setValue(self._widget_config.y)
            if "width" in self._property_widgets:
                self._property_widgets["width"].setValue(self._widget_config.width)
            if "height" in self._property_widgets:
                self._property_widgets["height"].setValue(self._widget_config.height)

            # Update widget properties
            for name, value in self._widget_config.properties.items():
                if name in self._property_widgets:
                    widget = self._property_widgets[name]
                    if isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDoubleSpinBox):
                        widget.setValue(float(value))
                    elif isinstance(widget, QLineEdit):
                        widget.setText(str(value))
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(str(value))
                    elif isinstance(widget, ColorButton):
                        widget.color = str(value)
        finally:
            self._updating = False

    def _group_style(self) -> str:
        """Get group box style."""
        return """
            QGroupBox {
                color: #aaa;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 12px;
                padding: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #bbb;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #ddd;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                border-color: #0078d4;
            }
        """
