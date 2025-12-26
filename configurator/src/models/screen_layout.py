# Screen Layout Models
"""Models for screen layouts and widget configurations."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
import json

from .widget_types import WidgetType, get_widget_definition


@dataclass
class WidgetConfig:
    """Configuration for a single widget on a screen."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    widget_type: WidgetType = WidgetType.CUSTOM_TEXT
    name: str = ""
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 100
    z_index: int = 0
    visible: bool = True
    locked: bool = False
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Set default name if not provided
        if not self.name:
            definition = get_widget_definition(self.widget_type)
            if definition:
                self.name = definition.display_name

        # Initialize default properties from widget definition
        definition = get_widget_definition(self.widget_type)
        if definition:
            for prop in definition.properties:
                if prop.name not in self.properties:
                    self.properties[prop.name] = prop.default_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "widget_type": self.widget_type.value,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "z_index": self.z_index,
            "visible": self.visible,
            "locked": self.locked,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WidgetConfig":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            widget_type=WidgetType(data["widget_type"]),
            name=data.get("name", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 100),
            height=data.get("height", 100),
            z_index=data.get("z_index", 0),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            properties=data.get("properties", {}),
        )

    def get_bounds(self) -> tuple:
        """Get widget bounds (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    def set_bounds(self, x: int, y: int, width: int, height: int) -> None:
        """Set widget bounds."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains_point(self, px: int, py: int) -> bool:
        """Check if point is inside widget bounds."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)


@dataclass
class ScreenLayout:
    """Configuration for a single screen layout."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Main Screen"
    width: int = 1024
    height: int = 600
    background_color: str = "#000000"
    widgets: List[WidgetConfig] = field(default_factory=list)

    # Grid settings
    grid_columns: int = 24
    grid_rows: int = 12
    grid_visible: bool = True
    snap_to_grid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "background_color": self.background_color,
            "grid_columns": self.grid_columns,
            "grid_rows": self.grid_rows,
            "grid_visible": self.grid_visible,
            "snap_to_grid": self.snap_to_grid,
            "widgets": [w.to_dict() for w in self.widgets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScreenLayout":
        """Create from dictionary."""
        widgets = [WidgetConfig.from_dict(w) for w in data.get("widgets", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Screen"),
            width=data.get("width", 1024),
            height=data.get("height", 600),
            background_color=data.get("background_color", "#000000"),
            grid_columns=data.get("grid_columns", 24),
            grid_rows=data.get("grid_rows", 12),
            grid_visible=data.get("grid_visible", True),
            snap_to_grid=data.get("snap_to_grid", True),
            widgets=widgets,
        )

    def add_widget(self, widget: WidgetConfig) -> None:
        """Add a widget to the screen."""
        # Set z-index to be on top
        if self.widgets:
            widget.z_index = max(w.z_index for w in self.widgets) + 1
        self.widgets.append(widget)

    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget by ID."""
        for i, w in enumerate(self.widgets):
            if w.id == widget_id:
                del self.widgets[i]
                return True
        return False

    def get_widget(self, widget_id: str) -> Optional[WidgetConfig]:
        """Get a widget by ID."""
        for w in self.widgets:
            if w.id == widget_id:
                return w
        return None

    def get_widgets_at_point(self, x: int, y: int) -> List[WidgetConfig]:
        """Get all widgets at a point, sorted by z-index (top first)."""
        widgets = [w for w in self.widgets if w.contains_point(x, y)]
        return sorted(widgets, key=lambda w: w.z_index, reverse=True)

    def get_cell_size(self) -> tuple:
        """Get grid cell size in pixels."""
        cell_w = self.width // self.grid_columns
        cell_h = self.height // self.grid_rows
        return (cell_w, cell_h)

    def snap_to_grid_position(self, x: int, y: int) -> tuple:
        """Snap coordinates to nearest grid position."""
        cell_w, cell_h = self.get_cell_size()
        snapped_x = round(x / cell_w) * cell_w
        snapped_y = round(y / cell_h) * cell_h
        return (snapped_x, snapped_y)

    def bring_to_front(self, widget_id: str) -> None:
        """Bring widget to front (highest z-index)."""
        widget = self.get_widget(widget_id)
        if widget:
            max_z = max((w.z_index for w in self.widgets), default=0)
            widget.z_index = max_z + 1

    def send_to_back(self, widget_id: str) -> None:
        """Send widget to back (lowest z-index)."""
        widget = self.get_widget(widget_id)
        if widget:
            min_z = min((w.z_index for w in self.widgets), default=0)
            widget.z_index = min_z - 1

    def duplicate_widget(self, widget_id: str, offset: int = 20) -> Optional[WidgetConfig]:
        """Duplicate a widget with offset."""
        original = self.get_widget(widget_id)
        if not original:
            return None

        new_widget = WidgetConfig(
            widget_type=original.widget_type,
            name=f"{original.name} (copy)",
            x=original.x + offset,
            y=original.y + offset,
            width=original.width,
            height=original.height,
            properties=original.properties.copy(),
        )
        self.add_widget(new_widget)
        return new_widget


def create_default_screen(name: str = "Main Screen") -> ScreenLayout:
    """Create a default screen layout with basic widgets."""
    screen = ScreenLayout(name=name)

    # Add default widgets
    # RPM Gauge (center)
    rpm_gauge = WidgetConfig(
        widget_type=WidgetType.RPM_GAUGE,
        x=412,
        y=200,
        width=200,
        height=200,
    )
    screen.add_widget(rpm_gauge)

    # Gear Indicator (center-right of RPM)
    gear = WidgetConfig(
        widget_type=WidgetType.GEAR_INDICATOR,
        x=620,
        y=250,
        width=80,
        height=100,
    )
    screen.add_widget(gear)

    # Shift Lights (top center)
    shift_lights = WidgetConfig(
        widget_type=WidgetType.SHIFT_LIGHTS,
        x=312,
        y=50,
        width=400,
        height=40,
    )
    screen.add_widget(shift_lights)

    # Speedometer (left)
    speedometer = WidgetConfig(
        widget_type=WidgetType.SPEEDOMETER,
        x=100,
        y=220,
        width=180,
        height=180,
    )
    screen.add_widget(speedometer)

    # Temp gauges (bottom left)
    coolant = WidgetConfig(
        widget_type=WidgetType.TEMP_GAUGE,
        name="Coolant Temp",
        x=50,
        y=450,
        width=100,
        height=100,
        properties={"temp_source": "coolant", "data_source": "coolant_temp"},
    )
    screen.add_widget(coolant)

    oil = WidgetConfig(
        widget_type=WidgetType.TEMP_GAUGE,
        name="Oil Temp",
        x=170,
        y=450,
        width=100,
        height=100,
        properties={"temp_source": "oil", "data_source": "oil_temp"},
    )
    screen.add_widget(oil)

    # G-Force meter (right)
    g_meter = WidgetConfig(
        widget_type=WidgetType.G_FORCE_METER,
        x=800,
        y=220,
        width=150,
        height=150,
    )
    screen.add_widget(g_meter)

    # Lap timer (bottom center)
    lap_timer = WidgetConfig(
        widget_type=WidgetType.LAP_TIMER,
        x=412,
        y=500,
        width=200,
        height=80,
    )
    screen.add_widget(lap_timer)

    return screen
