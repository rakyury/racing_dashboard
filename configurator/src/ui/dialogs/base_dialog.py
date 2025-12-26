# Base Settings Dialog
"""Base class for configuration dialogs."""

from typing import Optional, Any, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QFrame, QPushButton, QScrollArea,
    QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit,
    QCheckBox, QSlider, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal


class BaseSettingsDialog(QDialog):
    """
    Base class for all settings dialogs.
    Provides consistent styling and common functionality.
    """

    settings_changed = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._modified = False
        self._widgets = {}  # Store widgets for easy access

        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Content area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #2d2d2d; }")

        content_widget = QWidget()
        self._content_layout = QVBoxLayout(content_widget)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)

        # Subclass adds content here
        self._create_content()
        self._content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Footer with buttons
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create dialog header."""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-bottom: 1px solid #3d3d3d;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)

        title_label = QLabel(self._title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        layout.addWidget(title_label)
        layout.addStretch()

        return header

    def _create_footer(self) -> QWidget:
        """Create dialog footer with buttons."""
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-top: 1px solid #3d3d3d;
            }
        """)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(16, 10, 16, 10)

        # Reset button
        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.setStyleSheet(self._button_style("#555"))
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self._reset_btn)

        layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet(self._button_style("#555"))
        self._cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self._cancel_btn)

        # Apply button
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet(self._button_style("#0078d4"))
        self._apply_btn.clicked.connect(self._apply_and_accept)
        layout.addWidget(self._apply_btn)

        return footer

    def _button_style(self, bg_color: str) -> str:
        """Get button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(bg_color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(bg_color)};
            }}
        """

    @staticmethod
    def _lighten_color(color: str) -> str:
        """Lighten a hex color."""
        if color.startswith("#"):
            # Handle 3-digit hex colors (#RGB -> #RRGGBB)
            if len(color) == 4:
                color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
            r = min(255, int(color[1:3], 16) + 20)
            g = min(255, int(color[3:5], 16) + 20)
            b = min(255, int(color[5:7], 16) + 20)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color

    @staticmethod
    def _darken_color(color: str) -> str:
        """Darken a hex color."""
        if color.startswith("#"):
            # Handle 3-digit hex colors (#RGB -> #RRGGBB)
            if len(color) == 4:
                color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
            r = max(0, int(color[1:3], 16) - 20)
            g = max(0, int(color[3:5], 16) - 20)
            b = max(0, int(color[5:7], 16) - 20)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color

    def _create_content(self) -> None:
        """Override in subclass to create dialog content."""
        pass

    def _reset_to_defaults(self) -> None:
        """Override in subclass to reset settings."""
        pass

    def _apply_and_accept(self) -> None:
        """Apply settings and close dialog."""
        self._apply_settings()
        self.settings_changed.emit()
        self.accept()

    def _apply_settings(self) -> None:
        """Override in subclass to apply settings."""
        pass

    # Helper methods for creating form controls

    def _create_group(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #ccc;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        return group

    def _create_form_layout(self) -> QFormLayout:
        """Create a form layout with consistent styling."""
        layout = QFormLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        return layout

    def _create_label(self, text: str) -> QLabel:
        """Create a styled label."""
        label = QLabel(text)
        label.setStyleSheet("color: #aaa; font-size: 12px;")
        return label

    def _create_spinbox(self, min_val: int, max_val: int, value: int,
                       suffix: str = "", step: int = 1) -> QSpinBox:
        """Create a styled spin box."""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        spinbox.setSingleStep(step)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setStyleSheet(self._input_style())
        spinbox.valueChanged.connect(self._on_value_changed)
        return spinbox

    def _create_double_spinbox(self, min_val: float, max_val: float, value: float,
                               decimals: int = 2, suffix: str = "") -> QDoubleSpinBox:
        """Create a styled double spin box."""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        spinbox.setDecimals(decimals)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setStyleSheet(self._input_style())
        spinbox.valueChanged.connect(self._on_value_changed)
        return spinbox

    def _create_combobox(self, items: list, current: str = "") -> QComboBox:
        """Create a styled combo box."""
        combo = QComboBox()
        combo.addItems(items)
        if current and current in items:
            combo.setCurrentText(current)
        combo.setStyleSheet(self._combobox_style())
        combo.currentTextChanged.connect(self._on_value_changed)
        return combo

    def _create_lineedit(self, text: str = "", placeholder: str = "") -> QLineEdit:
        """Create a styled line edit."""
        edit = QLineEdit(text)
        if placeholder:
            edit.setPlaceholderText(placeholder)
        edit.setStyleSheet(self._input_style())
        edit.textChanged.connect(self._on_value_changed)
        return edit

    def _create_checkbox(self, text: str, checked: bool = False) -> QCheckBox:
        """Create a styled checkbox."""
        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #ccc;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #555;
                border-radius: 3px;
                background: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
            QCheckBox::indicator:hover {
                border-color: #0078d4;
            }
        """)
        checkbox.stateChanged.connect(self._on_value_changed)
        return checkbox

    def _create_slider(self, min_val: int, max_val: int, value: int) -> QSlider:
        """Create a styled horizontal slider."""
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(value)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #444;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 3px;
            }
        """)
        slider.valueChanged.connect(self._on_value_changed)
        return slider

    def _input_style(self) -> str:
        """Get input widget stylesheet."""
        return """
            QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #fff;
                min-width: 120px;
                font-size: 12px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border-color: #0078d4;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #555;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 1px solid #555;
            }
        """

    def _combobox_style(self) -> str:
        """Get combobox stylesheet."""
        return """
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #fff;
                min-width: 150px;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                border: 1px solid #555;
                selection-background-color: #0078d4;
                color: #fff;
            }
        """

    def _on_value_changed(self, *args) -> None:
        """Mark dialog as modified when any value changes."""
        self._modified = True


class SettingsRow(QWidget):
    """Helper widget for a settings row with label, control, and optional description."""

    def __init__(self, label: str, control: QWidget, description: str = "", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Main row
        row = QHBoxLayout()
        row.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #ccc; font-size: 12px;")
        label_widget.setMinimumWidth(140)
        row.addWidget(label_widget)

        row.addWidget(control)
        row.addStretch()

        layout.addLayout(row)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #888; font-size: 11px; padding-left: 152px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
