# Template Selection Dialog
"""Dialog for selecting a screen template when creating new project."""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QFrame, QGroupBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush

from models.screen_templates import (
    ScreenTemplate, TemplateCategory,
    get_all_templates, get_templates_by_category
)


class TemplatePreview(QFrame):
    """Widget showing a template preview."""

    clicked = pyqtSignal(object)  # ScreenTemplate

    def __init__(self, template: ScreenTemplate, parent=None):
        super().__init__(parent)
        self._template = template
        self._selected = False

        self.setFixedSize(200, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Preview area
        self._preview = TemplatePreviewCanvas(template)
        self._preview.setFixedHeight(90)
        layout.addWidget(self._preview)

        # Name
        name_label = QLabel(template.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; color: #fff;")
        layout.addWidget(name_label)

        # Screen count
        screen_count = len(template.screens)
        screens_label = QLabel(f"{screen_count} screen{'s' if screen_count != 1 else ''}")
        screens_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screens_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(screens_label)

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._template)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        self._update_style()

    def _update_style(self) -> None:
        """Update frame style."""
        if self._selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a3a3a;
                    border: 2px solid #0078d4;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border: 2px solid #444;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border-color: #666;
                    background-color: #353535;
                }
            """)


class TemplatePreviewCanvas(QWidget):
    """Canvas showing miniature preview of template layout."""

    def __init__(self, template: ScreenTemplate, parent=None):
        super().__init__(parent)
        self._template = template
        self.setMinimumHeight(80)

    def paintEvent(self, event):
        """Paint the preview."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        if not self._template.screens:
            return

        # Draw first screen preview
        screen = self._template.screens[0]

        # Calculate scale
        margin = 4
        available_w = self.width() - margin * 2
        available_h = self.height() - margin * 2

        scale_x = available_w / screen.width
        scale_y = available_h / screen.height
        scale = min(scale_x, scale_y)

        # Center offset
        preview_w = screen.width * scale
        preview_h = screen.height * scale
        offset_x = margin + (available_w - preview_w) / 2
        offset_y = margin + (available_h - preview_h) / 2

        # Draw screen background
        painter.fillRect(
            int(offset_x), int(offset_y),
            int(preview_w), int(preview_h),
            QColor("#222")
        )

        # Draw widgets
        widget_colors = {
            "rpm": "#4CAF50",
            "speed": "#2196F3",
            "temp": "#FF9800",
            "fuel": "#9C27B0",
            "gear": "#E91E63",
            "lap": "#00BCD4",
            "delta": "#FFEB3B",
            "g_meter": "#795548",
            "bar": "#607D8B",
            "default": "#555"
        }

        for widget in screen.widgets:
            # Determine color based on widget type
            widget_type = widget.widget_type.value.lower()
            color = widget_colors.get("default")

            if "rpm" in widget_type or "tach" in widget_type:
                color = widget_colors["rpm"]
            elif "speed" in widget_type:
                color = widget_colors["speed"]
            elif "temp" in widget_type:
                color = widget_colors["temp"]
            elif "fuel" in widget_type:
                color = widget_colors["fuel"]
            elif "gear" in widget_type:
                color = widget_colors["gear"]
            elif "lap" in widget_type or "timer" in widget_type:
                color = widget_colors["lap"]
            elif "delta" in widget_type:
                color = widget_colors["delta"]
            elif "g_meter" in widget_type:
                color = widget_colors["g_meter"]
            elif "bar" in widget_type:
                color = widget_colors["bar"]

            # Draw widget rectangle
            x = offset_x + widget.x * scale
            y = offset_y + widget.y * scale
            w = widget.width * scale
            h = widget.height * scale

            painter.setPen(QPen(QColor(color).darker(120), 1))
            painter.setBrush(QBrush(QColor(color)))
            painter.drawRoundedRect(int(x), int(y), int(w), int(h), 2, 2)


class TemplateSelectionDialog(QDialog):
    """Dialog for selecting a template."""

    template_selected = pyqtSignal(object)  # ScreenTemplate

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_template: Optional[ScreenTemplate] = None
        self._preview_widgets: List[TemplatePreview] = []

        self.setWindowTitle("Select Template")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
            }
            QLabel {
                color: #ddd;
            }
            QGroupBox {
                color: #aaa;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 12px;
                padding: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ddd;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #454545;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
            }
            QPushButton#primaryBtn {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QPushButton#primaryBtn:hover {
                background-color: #1084d8;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #006cbd;
            }
        """)

        self._setup_ui()
        self._populate_templates()

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Choose a Template")
        header.setFont(QFont("", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #fff; padding: 8px;")
        layout.addWidget(header)

        # Description
        desc = QLabel("Select a starting template for your dashboard. You can customize it later.")
        desc.setStyleSheet("color: #888; padding: 0 8px;")
        layout.addWidget(desc)

        # Scroll area for templates
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._template_container = QWidget()
        self._template_layout = QVBoxLayout(self._template_container)
        self._template_layout.setSpacing(16)

        scroll.setWidget(self._template_container)
        layout.addWidget(scroll, 1)

        # Description panel
        self._desc_panel = QFrame()
        self._desc_panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        desc_layout = QVBoxLayout(self._desc_panel)

        self._desc_title = QLabel("No template selected")
        self._desc_title.setStyleSheet("font-weight: bold; color: #fff;")
        desc_layout.addWidget(self._desc_title)

        self._desc_text = QLabel("")
        self._desc_text.setStyleSheet("color: #aaa;")
        self._desc_text.setWordWrap(True)
        desc_layout.addWidget(self._desc_text)

        layout.addWidget(self._desc_panel)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._select_btn = QPushButton("Select Template")
        self._select_btn.setObjectName("primaryBtn")
        self._select_btn.setEnabled(False)
        self._select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(self._select_btn)

        layout.addLayout(btn_layout)

    def _populate_templates(self) -> None:
        """Populate template categories."""
        templates_by_cat = get_templates_by_category()

        for category, templates in templates_by_cat.items():
            group = QGroupBox(category.value)
            group_layout = QHBoxLayout(group)
            group_layout.setSpacing(12)

            for template in templates:
                preview = TemplatePreview(template)
                preview.clicked.connect(self._on_template_clicked)
                group_layout.addWidget(preview)
                self._preview_widgets.append(preview)

            group_layout.addStretch()
            self._template_layout.addWidget(group)

        self._template_layout.addStretch()

    def _on_template_clicked(self, template: ScreenTemplate) -> None:
        """Handle template selection."""
        self._selected_template = template

        # Update selection state
        for preview in self._preview_widgets:
            preview.set_selected(preview._template == template)

        # Update description
        self._desc_title.setText(template.name)
        self._desc_text.setText(template.description)

        # Enable select button
        self._select_btn.setEnabled(True)

    def _on_select(self) -> None:
        """Handle select button click."""
        if self._selected_template:
            self.template_selected.emit(self._selected_template)
            self.accept()

    def get_selected_template(self) -> Optional[ScreenTemplate]:
        """Get the selected template."""
        return self._selected_template


def show_template_dialog(parent=None) -> Optional[ScreenTemplate]:
    """Show template selection dialog and return selected template."""
    dialog = TemplateSelectionDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_selected_template()
    return None
