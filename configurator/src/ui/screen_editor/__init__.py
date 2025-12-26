# Screen Editor package
"""Visual screen editor components."""

from .canvas import ScreenCanvas, WidgetItem, GridOverlay
from .widget_palette import WidgetPalette, CompactWidgetPalette
from .property_panel import PropertyPanel
from .screen_editor_widget import ScreenEditorWidget

__all__ = [
    'ScreenCanvas',
    'WidgetItem',
    'GridOverlay',
    'WidgetPalette',
    'CompactWidgetPalette',
    'PropertyPanel',
    'ScreenEditorWidget',
]
