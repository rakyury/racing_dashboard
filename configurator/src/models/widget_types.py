# Widget Types
"""Widget type definitions for Racing Dashboard screen layouts."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


class WidgetType(Enum):
    """Available widget types for screen editor."""

    # Gauges
    RPM_GAUGE = "rpm_gauge"
    SPEEDOMETER = "speedometer"
    TEMP_GAUGE = "temp_gauge"
    FUEL_GAUGE = "fuel_gauge"
    PRESSURE_GAUGE = "pressure_gauge"
    BOOST_GAUGE = "boost_gauge"

    # Indicators
    GEAR_INDICATOR = "gear_indicator"
    SHIFT_LIGHTS = "shift_lights"
    STATUS_PILL = "status_pill"
    WARNING_LIGHT = "warning_light"
    LED_INDICATOR = "led_indicator"

    # Meters
    G_FORCE_METER = "g_force_meter"
    THROTTLE_BAR = "throttle_bar"
    BRAKE_BAR = "brake_bar"
    AFR_BAR = "afr_bar"

    # Timers
    LAP_TIMER = "lap_timer"
    DELTA_DISPLAY = "delta_display"
    SECTOR_TIMES = "sector_times"
    BEST_LAP = "best_lap"

    # Text & Data
    CUSTOM_TEXT = "custom_text"
    VARIABLE_DISPLAY = "variable_display"
    NUMERIC_DISPLAY = "numeric_display"

    # Misc
    IMAGE = "image"
    RECTANGLE = "rectangle"
    LINE = "line"


@dataclass
class WidgetProperty:
    """Definition of a widget property for the property panel."""

    name: str
    display_name: str
    property_type: str  # "int", "float", "string", "color", "bool", "enum", "data_source"
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[str]] = None
    description: str = ""


@dataclass
class WidgetDefinition:
    """Definition of a widget type with its properties."""

    widget_type: WidgetType
    display_name: str
    category: str
    icon: str
    default_width: int
    default_height: int
    min_width: int = 20
    min_height: int = 20
    properties: List[WidgetProperty] = field(default_factory=list)
    description: str = ""


# Widget definitions registry
WIDGET_DEFINITIONS: Dict[WidgetType, WidgetDefinition] = {
    WidgetType.RPM_GAUGE: WidgetDefinition(
        widget_type=WidgetType.RPM_GAUGE,
        display_name="RPM Gauge",
        category="Gauges",
        icon="gauge_rpm.png",
        default_width=200,
        default_height=200,
        properties=[
            WidgetProperty("min_rpm", "Min RPM", "int", 0, 0, 20000),
            WidgetProperty("max_rpm", "Max RPM", "int", 8000, 1000, 20000),
            WidgetProperty("redline_rpm", "Redline RPM", "int", 7000, 1000, 20000),
            WidgetProperty("warning_rpm", "Warning RPM", "int", 6500, 1000, 20000),
            WidgetProperty("data_source", "Data Source", "data_source", "engine_rpm"),
            WidgetProperty("show_digital", "Show Digital", "bool", True),
            WidgetProperty("needle_color", "Needle Color", "color", "#ff0000"),
        ],
        description="Circular RPM tachometer with redline indication"
    ),

    WidgetType.SPEEDOMETER: WidgetDefinition(
        widget_type=WidgetType.SPEEDOMETER,
        display_name="Speedometer",
        category="Gauges",
        icon="gauge_speed.png",
        default_width=180,
        default_height=180,
        properties=[
            WidgetProperty("max_speed", "Max Speed", "int", 300, 100, 500),
            WidgetProperty("units", "Units", "enum", "km/h", enum_values=["km/h", "mph"]),
            WidgetProperty("data_source", "Data Source", "data_source", "vehicle_speed"),
            WidgetProperty("show_digital", "Show Digital", "bool", True),
        ],
        description="Vehicle speed gauge"
    ),

    WidgetType.GEAR_INDICATOR: WidgetDefinition(
        widget_type=WidgetType.GEAR_INDICATOR,
        display_name="Gear Indicator",
        category="Indicators",
        icon="gear.png",
        default_width=80,
        default_height=100,
        properties=[
            WidgetProperty("font_size", "Font Size", "int", 72, 24, 200),
            WidgetProperty("data_source", "Data Source", "data_source", "gear"),
            WidgetProperty("neutral_text", "Neutral Text", "string", "N"),
            WidgetProperty("reverse_text", "Reverse Text", "string", "R"),
            WidgetProperty("text_color", "Text Color", "color", "#ffffff"),
        ],
        description="Current gear number display"
    ),

    WidgetType.SHIFT_LIGHTS: WidgetDefinition(
        widget_type=WidgetType.SHIFT_LIGHTS,
        display_name="Shift Lights",
        category="Indicators",
        icon="shift_lights.png",
        default_width=400,
        default_height=40,
        properties=[
            WidgetProperty("led_count", "LED Count", "int", 10, 3, 20),
            WidgetProperty("start_rpm", "Start RPM", "int", 5000, 1000, 15000),
            WidgetProperty("shift_rpm", "Shift RPM", "int", 7000, 1000, 20000),
            WidgetProperty("data_source", "Data Source", "data_source", "engine_rpm"),
            WidgetProperty("color_low", "Color Low", "color", "#00ff00"),
            WidgetProperty("color_mid", "Color Mid", "color", "#ffff00"),
            WidgetProperty("color_high", "Color High", "color", "#ff0000"),
            WidgetProperty("blink_at_shift", "Blink at Shift", "bool", True),
        ],
        description="Sequential shift light bar"
    ),

    WidgetType.TEMP_GAUGE: WidgetDefinition(
        widget_type=WidgetType.TEMP_GAUGE,
        display_name="Temperature Gauge",
        category="Gauges",
        icon="gauge_temp.png",
        default_width=120,
        default_height=120,
        properties=[
            WidgetProperty("temp_source", "Source", "enum", "coolant",
                          enum_values=["coolant", "oil", "intake_air", "exhaust", "custom"]),
            WidgetProperty("min_temp", "Min Temp", "int", 0, -50, 200),
            WidgetProperty("max_temp", "Max Temp", "int", 150, 50, 300),
            WidgetProperty("warning_temp", "Warning Temp", "int", 110, 50, 200),
            WidgetProperty("critical_temp", "Critical Temp", "int", 120, 50, 250),
            WidgetProperty("units", "Units", "enum", "C", enum_values=["C", "F"]),
            WidgetProperty("data_source", "Data Source", "data_source", "coolant_temp"),
        ],
        description="Temperature gauge for coolant, oil, etc."
    ),

    WidgetType.G_FORCE_METER: WidgetDefinition(
        widget_type=WidgetType.G_FORCE_METER,
        display_name="G-Force Meter",
        category="Meters",
        icon="g_force.png",
        default_width=150,
        default_height=150,
        properties=[
            WidgetProperty("max_g", "Max G", "float", 2.0, 0.5, 5.0),
            WidgetProperty("style", "Style", "enum", "dot", enum_values=["dot", "trace", "bar"]),
            WidgetProperty("show_values", "Show Values", "bool", True),
            WidgetProperty("lateral_source", "Lateral Source", "data_source", "g_lateral"),
            WidgetProperty("longitudinal_source", "Longitudinal Source", "data_source", "g_longitudinal"),
            WidgetProperty("dot_color", "Dot Color", "color", "#00ff00"),
        ],
        description="2D G-force visualization"
    ),

    WidgetType.STATUS_PILL: WidgetDefinition(
        widget_type=WidgetType.STATUS_PILL,
        display_name="Status Pill",
        category="Indicators",
        icon="status_pill.png",
        default_width=100,
        default_height=36,
        properties=[
            WidgetProperty("label", "Label", "string", "STATUS"),
            WidgetProperty("data_source", "Data Source", "data_source", ""),
            WidgetProperty("on_color", "On Color", "color", "#00ff00"),
            WidgetProperty("off_color", "Off Color", "color", "#333333"),
            WidgetProperty("warning_color", "Warning Color", "color", "#ff8c00"),
            WidgetProperty("error_color", "Error Color", "color", "#ff0000"),
        ],
        description="Status indicator pill"
    ),

    WidgetType.LAP_TIMER: WidgetDefinition(
        widget_type=WidgetType.LAP_TIMER,
        display_name="Lap Timer",
        category="Timers",
        icon="lap_timer.png",
        default_width=200,
        default_height=80,
        properties=[
            WidgetProperty("show_current", "Show Current", "bool", True),
            WidgetProperty("show_best", "Show Best", "bool", True),
            WidgetProperty("show_delta", "Show Delta", "bool", True),
            WidgetProperty("delta_positive_color", "Delta + Color", "color", "#ff0000"),
            WidgetProperty("delta_negative_color", "Delta - Color", "color", "#00ff00"),
            WidgetProperty("font_size", "Font Size", "int", 36, 12, 72),
        ],
        description="Lap time display with delta"
    ),

    WidgetType.CUSTOM_TEXT: WidgetDefinition(
        widget_type=WidgetType.CUSTOM_TEXT,
        display_name="Custom Text",
        category="Text",
        icon="text.png",
        default_width=150,
        default_height=40,
        properties=[
            WidgetProperty("text", "Text", "string", "Label"),
            WidgetProperty("font_size", "Font Size", "int", 24, 8, 120),
            WidgetProperty("font_family", "Font", "enum", "Roboto",
                          enum_values=["Roboto", "Roboto Mono", "Arial", "Consolas"]),
            WidgetProperty("text_color", "Color", "color", "#ffffff"),
            WidgetProperty("alignment", "Alignment", "enum", "center",
                          enum_values=["left", "center", "right"]),
            WidgetProperty("bold", "Bold", "bool", False),
        ],
        description="Static or dynamic text label"
    ),

    WidgetType.FUEL_GAUGE: WidgetDefinition(
        widget_type=WidgetType.FUEL_GAUGE,
        display_name="Fuel Gauge",
        category="Gauges",
        icon="gauge_fuel.png",
        default_width=120,
        default_height=120,
        properties=[
            WidgetProperty("tank_capacity", "Tank Capacity (L)", "float", 60.0, 10.0, 200.0),
            WidgetProperty("low_warning", "Low Warning (%)", "int", 15, 5, 30),
            WidgetProperty("data_source", "Data Source", "data_source", "fuel_level"),
            WidgetProperty("style", "Style", "enum", "arc", enum_values=["arc", "bar", "digital"]),
        ],
        description="Fuel level gauge"
    ),

    WidgetType.VARIABLE_DISPLAY: WidgetDefinition(
        widget_type=WidgetType.VARIABLE_DISPLAY,
        display_name="Variable Display",
        category="Text",
        icon="variable.png",
        default_width=120,
        default_height=60,
        properties=[
            WidgetProperty("label", "Label", "string", "Value"),
            WidgetProperty("data_source", "Data Source", "data_source", ""),
            WidgetProperty("units", "Units", "string", ""),
            WidgetProperty("decimals", "Decimals", "int", 1, 0, 4),
            WidgetProperty("font_size", "Font Size", "int", 28, 12, 72),
            WidgetProperty("show_label", "Show Label", "bool", True),
        ],
        description="Numeric variable display with label"
    ),
}


def get_widget_definition(widget_type: WidgetType) -> Optional[WidgetDefinition]:
    """Get the definition for a widget type."""
    return WIDGET_DEFINITIONS.get(widget_type)


def get_widgets_by_category() -> Dict[str, List[WidgetDefinition]]:
    """Get widget definitions organized by category."""
    categories: Dict[str, List[WidgetDefinition]] = {}
    for definition in WIDGET_DEFINITIONS.values():
        if definition.category not in categories:
            categories[definition.category] = []
        categories[definition.category].append(definition)
    return categories
