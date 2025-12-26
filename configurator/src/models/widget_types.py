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

    # Charts & Graphs
    LINE_GRAPH = "line_graph"
    BAR_CHART = "bar_chart"
    HISTOGRAM = "histogram"
    PIE_CHART = "pie_chart"

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

    WidgetType.PRESSURE_GAUGE: WidgetDefinition(
        widget_type=WidgetType.PRESSURE_GAUGE,
        display_name="Pressure Gauge",
        category="Gauges",
        icon="gauge_pressure.png",
        default_width=120,
        default_height=120,
        properties=[
            WidgetProperty("pressure_type", "Type", "enum", "oil",
                          enum_values=["oil", "fuel", "brake", "boost", "custom"]),
            WidgetProperty("min_pressure", "Min", "float", 0, 0, 100),
            WidgetProperty("max_pressure", "Max", "float", 10, 1, 100),
            WidgetProperty("warning_low", "Warning Low", "float", 1.5, 0, 50),
            WidgetProperty("warning_high", "Warning High", "float", 8, 1, 100),
            WidgetProperty("units", "Units", "enum", "bar", enum_values=["bar", "psi", "kPa"]),
            WidgetProperty("data_source", "Data Source", "data_source", "oil_pressure"),
        ],
        description="Pressure gauge for oil, fuel, brake"
    ),

    WidgetType.BOOST_GAUGE: WidgetDefinition(
        widget_type=WidgetType.BOOST_GAUGE,
        display_name="Boost Gauge",
        category="Gauges",
        icon="gauge_boost.png",
        default_width=150,
        default_height=150,
        properties=[
            WidgetProperty("min_boost", "Min (vacuum)", "float", -1.0, -1.5, 0),
            WidgetProperty("max_boost", "Max (boost)", "float", 2.5, 0.5, 5.0),
            WidgetProperty("target_boost", "Target Boost", "float", 1.5, 0, 4.0),
            WidgetProperty("units", "Units", "enum", "bar", enum_values=["bar", "psi", "kPa"]),
            WidgetProperty("data_source", "Data Source", "data_source", "boost_pressure"),
            WidgetProperty("show_peak", "Show Peak", "bool", True),
        ],
        description="Turbo/supercharger boost pressure gauge"
    ),

    WidgetType.WARNING_LIGHT: WidgetDefinition(
        widget_type=WidgetType.WARNING_LIGHT,
        display_name="Warning Light",
        category="Indicators",
        icon="warning.png",
        default_width=50,
        default_height=50,
        properties=[
            WidgetProperty("icon_type", "Icon", "enum", "engine",
                          enum_values=["engine", "oil", "temp", "battery", "fuel", "abs", "custom"]),
            WidgetProperty("data_source", "Data Source", "data_source", ""),
            WidgetProperty("threshold", "Threshold", "float", 1.0, 0, 1000),
            WidgetProperty("condition", "Condition", "enum", "greater",
                          enum_values=["greater", "less", "equal", "not_equal"]),
            WidgetProperty("active_color", "Active Color", "color", "#ff0000"),
            WidgetProperty("inactive_color", "Inactive Color", "color", "#333333"),
            WidgetProperty("blink_when_active", "Blink", "bool", True),
        ],
        description="Conditional warning indicator"
    ),

    WidgetType.LED_INDICATOR: WidgetDefinition(
        widget_type=WidgetType.LED_INDICATOR,
        display_name="LED Indicator",
        category="Indicators",
        icon="led.png",
        default_width=30,
        default_height=30,
        properties=[
            WidgetProperty("label", "Label", "string", ""),
            WidgetProperty("data_source", "Data Source", "data_source", ""),
            WidgetProperty("on_color", "On Color", "color", "#00ff00"),
            WidgetProperty("off_color", "Off Color", "color", "#333333"),
            WidgetProperty("shape", "Shape", "enum", "circle", enum_values=["circle", "square", "rounded"]),
        ],
        description="Simple on/off LED indicator"
    ),

    WidgetType.THROTTLE_BAR: WidgetDefinition(
        widget_type=WidgetType.THROTTLE_BAR,
        display_name="Throttle Bar",
        category="Meters",
        icon="throttle.png",
        default_width=200,
        default_height=30,
        properties=[
            WidgetProperty("data_source", "Data Source", "data_source", "throttle_position"),
            WidgetProperty("orientation", "Orientation", "enum", "horizontal",
                          enum_values=["horizontal", "vertical"]),
            WidgetProperty("bar_color", "Bar Color", "color", "#00ff00"),
            WidgetProperty("show_percentage", "Show %", "bool", True),
        ],
        description="Throttle position bar"
    ),

    WidgetType.BRAKE_BAR: WidgetDefinition(
        widget_type=WidgetType.BRAKE_BAR,
        display_name="Brake Bar",
        category="Meters",
        icon="brake.png",
        default_width=200,
        default_height=30,
        properties=[
            WidgetProperty("data_source", "Data Source", "data_source", "brake_pressure"),
            WidgetProperty("orientation", "Orientation", "enum", "horizontal",
                          enum_values=["horizontal", "vertical"]),
            WidgetProperty("bar_color", "Bar Color", "color", "#ff0000"),
            WidgetProperty("show_percentage", "Show %", "bool", True),
        ],
        description="Brake pressure/position bar"
    ),

    WidgetType.AFR_BAR: WidgetDefinition(
        widget_type=WidgetType.AFR_BAR,
        display_name="AFR Bar",
        category="Meters",
        icon="afr.png",
        default_width=200,
        default_height=40,
        properties=[
            WidgetProperty("min_afr", "Min AFR", "float", 10.0, 8.0, 12.0),
            WidgetProperty("max_afr", "Max AFR", "float", 18.0, 14.0, 22.0),
            WidgetProperty("target_afr", "Target AFR", "float", 14.7, 10.0, 18.0),
            WidgetProperty("rich_color", "Rich Color", "color", "#00ff00"),
            WidgetProperty("lean_color", "Lean Color", "color", "#ff0000"),
            WidgetProperty("data_source", "Data Source", "data_source", "afr"),
            WidgetProperty("show_value", "Show Value", "bool", True),
        ],
        description="Air/Fuel Ratio bar with target"
    ),

    WidgetType.DELTA_DISPLAY: WidgetDefinition(
        widget_type=WidgetType.DELTA_DISPLAY,
        display_name="Delta Display",
        category="Timers",
        icon="delta.png",
        default_width=150,
        default_height=50,
        properties=[
            WidgetProperty("font_size", "Font Size", "int", 32, 16, 72),
            WidgetProperty("positive_color", "Slower Color", "color", "#ff0000"),
            WidgetProperty("negative_color", "Faster Color", "color", "#00ff00"),
            WidgetProperty("show_sign", "Show +/-", "bool", True),
        ],
        description="Lap time delta from best"
    ),

    WidgetType.SECTOR_TIMES: WidgetDefinition(
        widget_type=WidgetType.SECTOR_TIMES,
        display_name="Sector Times",
        category="Timers",
        icon="sectors.png",
        default_width=200,
        default_height=80,
        properties=[
            WidgetProperty("sector_count", "Sector Count", "int", 3, 1, 10),
            WidgetProperty("show_delta", "Show Delta", "bool", True),
            WidgetProperty("font_size", "Font Size", "int", 18, 10, 36),
            WidgetProperty("best_color", "Best Color", "color", "#ff00ff"),
            WidgetProperty("improved_color", "Improved Color", "color", "#00ff00"),
            WidgetProperty("slower_color", "Slower Color", "color", "#ffff00"),
        ],
        description="Sector time breakdown"
    ),

    WidgetType.BEST_LAP: WidgetDefinition(
        widget_type=WidgetType.BEST_LAP,
        display_name="Best Lap",
        category="Timers",
        icon="best_lap.png",
        default_width=180,
        default_height=50,
        properties=[
            WidgetProperty("font_size", "Font Size", "int", 28, 14, 60),
            WidgetProperty("label", "Label", "string", "BEST"),
            WidgetProperty("text_color", "Color", "color", "#ff00ff"),
            WidgetProperty("show_label", "Show Label", "bool", True),
        ],
        description="Best lap time display"
    ),

    WidgetType.NUMERIC_DISPLAY: WidgetDefinition(
        widget_type=WidgetType.NUMERIC_DISPLAY,
        display_name="Numeric Display",
        category="Text",
        icon="numeric.png",
        default_width=100,
        default_height=50,
        properties=[
            WidgetProperty("data_source", "Data Source", "data_source", ""),
            WidgetProperty("decimals", "Decimals", "int", 0, 0, 4),
            WidgetProperty("font_size", "Font Size", "int", 36, 12, 120),
            WidgetProperty("text_color", "Color", "color", "#ffffff"),
            WidgetProperty("prefix", "Prefix", "string", ""),
            WidgetProperty("suffix", "Suffix", "string", ""),
        ],
        description="Simple numeric value display"
    ),

    WidgetType.IMAGE: WidgetDefinition(
        widget_type=WidgetType.IMAGE,
        display_name="Image",
        category="Graphics",
        icon="image.png",
        default_width=100,
        default_height=100,
        properties=[
            WidgetProperty("image_path", "Image Path", "string", ""),
            WidgetProperty("fit_mode", "Fit Mode", "enum", "contain",
                          enum_values=["contain", "cover", "stretch", "none"]),
            WidgetProperty("opacity", "Opacity", "float", 1.0, 0.0, 1.0),
        ],
        description="Static image or logo"
    ),

    WidgetType.RECTANGLE: WidgetDefinition(
        widget_type=WidgetType.RECTANGLE,
        display_name="Rectangle",
        category="Graphics",
        icon="rectangle.png",
        default_width=100,
        default_height=60,
        properties=[
            WidgetProperty("fill_color", "Fill Color", "color", "#333333"),
            WidgetProperty("border_color", "Border Color", "color", "#666666"),
            WidgetProperty("border_width", "Border Width", "int", 1, 0, 10),
            WidgetProperty("corner_radius", "Corner Radius", "int", 0, 0, 50),
            WidgetProperty("opacity", "Opacity", "float", 1.0, 0.0, 1.0),
        ],
        description="Decorative rectangle shape"
    ),

    WidgetType.LINE: WidgetDefinition(
        widget_type=WidgetType.LINE,
        display_name="Line",
        category="Graphics",
        icon="line.png",
        default_width=100,
        default_height=2,
        min_height=1,
        properties=[
            WidgetProperty("line_color", "Color", "color", "#666666"),
            WidgetProperty("line_width", "Width", "int", 2, 1, 20),
            WidgetProperty("line_style", "Style", "enum", "solid",
                          enum_values=["solid", "dashed", "dotted"]),
        ],
        description="Decorative line separator"
    ),

    WidgetType.LINE_GRAPH: WidgetDefinition(
        widget_type=WidgetType.LINE_GRAPH,
        display_name="Line Graph",
        category="Charts",
        icon="graph_line.png",
        default_width=300,
        default_height=150,
        properties=[
            WidgetProperty("data_source", "Data Source", "data_source", "engine_rpm"),
            WidgetProperty("time_window", "Time Window (s)", "int", 30, 5, 300),
            WidgetProperty("min_value", "Min Value", "float", 0, -1000, 10000),
            WidgetProperty("max_value", "Max Value", "float", 8000, 0, 20000),
            WidgetProperty("auto_scale", "Auto Scale", "bool", True),
            WidgetProperty("line_color", "Line Color", "color", "#4FC3F7"),
            WidgetProperty("line_width", "Line Width", "int", 2, 1, 5),
            WidgetProperty("fill_area", "Fill Area", "bool", True),
            WidgetProperty("fill_opacity", "Fill Opacity", "float", 0.3, 0.0, 1.0),
            WidgetProperty("show_grid", "Show Grid", "bool", True),
            WidgetProperty("show_labels", "Show Labels", "bool", True),
            WidgetProperty("label", "Label", "string", ""),
        ],
        description="Real-time line graph for data over time"
    ),

    WidgetType.BAR_CHART: WidgetDefinition(
        widget_type=WidgetType.BAR_CHART,
        display_name="Bar Chart",
        category="Charts",
        icon="graph_bar.png",
        default_width=200,
        default_height=120,
        properties=[
            WidgetProperty("data_sources", "Data Sources", "string", ""),
            WidgetProperty("labels", "Labels", "string", ""),
            WidgetProperty("max_value", "Max Value", "float", 100, 0, 10000),
            WidgetProperty("bar_color", "Bar Color", "color", "#4CAF50"),
            WidgetProperty("bar_spacing", "Bar Spacing", "int", 4, 0, 20),
            WidgetProperty("orientation", "Orientation", "enum", "vertical",
                          enum_values=["vertical", "horizontal"]),
            WidgetProperty("show_values", "Show Values", "bool", True),
            WidgetProperty("show_labels", "Show Labels", "bool", True),
        ],
        description="Bar chart for comparing multiple values"
    ),

    WidgetType.HISTOGRAM: WidgetDefinition(
        widget_type=WidgetType.HISTOGRAM,
        display_name="Histogram",
        category="Charts",
        icon="graph_histogram.png",
        default_width=250,
        default_height=120,
        properties=[
            WidgetProperty("data_source", "Data Source", "data_source", "engine_rpm"),
            WidgetProperty("bin_count", "Bin Count", "int", 20, 5, 50),
            WidgetProperty("min_value", "Min Value", "float", 0, -1000, 10000),
            WidgetProperty("max_value", "Max Value", "float", 8000, 0, 20000),
            WidgetProperty("bar_color", "Bar Color", "color", "#FF9800"),
            WidgetProperty("show_stats", "Show Stats", "bool", True),
            WidgetProperty("sample_window", "Sample Window (s)", "int", 60, 10, 600),
        ],
        description="Value distribution histogram"
    ),

    WidgetType.PIE_CHART: WidgetDefinition(
        widget_type=WidgetType.PIE_CHART,
        display_name="Pie Chart",
        category="Charts",
        icon="graph_pie.png",
        default_width=150,
        default_height=150,
        properties=[
            WidgetProperty("data_sources", "Data Sources", "string", ""),
            WidgetProperty("labels", "Labels", "string", ""),
            WidgetProperty("colors", "Colors", "string", "#4CAF50,#2196F3,#FF9800,#E91E63"),
            WidgetProperty("show_labels", "Show Labels", "bool", True),
            WidgetProperty("show_percentages", "Show Percentages", "bool", True),
            WidgetProperty("donut_mode", "Donut Mode", "bool", False),
            WidgetProperty("donut_ratio", "Donut Ratio", "float", 0.5, 0.2, 0.8),
        ],
        description="Pie chart for proportional data"
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
