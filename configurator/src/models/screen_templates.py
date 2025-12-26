# Screen Templates
"""Predefined screen templates for Racing Dashboard."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum

from .widget_types import WidgetType
from .screen_layout import ScreenLayout, WidgetConfig

# Channel ID constants (matching firmware)
RD_CH_ENGINE_RPM = 100
RD_CH_VEHICLE_SPEED = 101
RD_CH_THROTTLE_POSITION = 102
RD_CH_COOLANT_TEMP = 103
RD_CH_OIL_TEMP = 104
RD_CH_OIL_PRESSURE = 105
RD_CH_FUEL_PRESSURE = 106
RD_CH_BOOST_PRESSURE = 107
RD_CH_AFR = 108
RD_CH_GEAR = 110
RD_CH_FUEL_LEVEL = 111
RD_CH_BRAKE_PRESSURE = 117
RD_CH_G_LATERAL = 123
RD_CH_G_LONGITUDINAL = 124

RD_CH_GPS_SPEED = 503

RD_CH_LAP_CURRENT_TIME = 550
RD_CH_LAP_LAST_TIME = 551
RD_CH_LAP_BEST_TIME = 552
RD_CH_LAP_DELTA = 553
RD_CH_LAP_NUMBER = 554


class TemplateCategory(Enum):
    """Template categories."""
    STREET = "Street"
    TRACK = "Track"
    DRAG = "Drag"
    DRIFT = "Drift"
    MINIMAL = "Minimal"
    CUSTOM = "Custom"


@dataclass
class ScreenTemplate:
    """Screen template definition."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    preview_image: str = ""
    screens: List[ScreenLayout] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "preview_image": self.preview_image,
            "screens": [screen.to_dict() for screen in self.screens],
        }


def _create_widget(
    widget_type: WidgetType,
    x: int, y: int,
    width: int, height: int,
    name: str = "",
    channel_id: int = 0,
    **extra_props
) -> WidgetConfig:
    """Helper to create widget config."""
    props = {}
    if channel_id:
        props["data_source"] = channel_id
    props.update(extra_props)

    return WidgetConfig(
        widget_type=widget_type,
        name=name or widget_type.value,
        x=x, y=y,
        width=width, height=height,
        properties=props
    )


# =============================================================================
# Street/Road Templates
# =============================================================================

def create_street_classic_template() -> ScreenTemplate:
    """Classic street dashboard - RPM, Speed, Temps."""
    screen = ScreenLayout(id=0, name="Main", width=800, height=480)

    # Large RPM gauge center-top
    screen.add_widget(_create_widget(
        WidgetType.RPM_GAUGE, 200, 20, 400, 200,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=8000, redline=7000
    ))

    # Speed left
    screen.add_widget(_create_widget(
        WidgetType.SPEEDOMETER, 30, 250, 180, 180,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        max_value=280
    ))

    # Coolant temp right
    screen.add_widget(_create_widget(
        WidgetType.TEMP_GAUGE, 590, 250, 180, 180,
        name="Coolant", channel_id=RD_CH_COOLANT_TEMP,
        min_value=50, max_value=130, warning_high=105
    ))

    # Fuel gauge bottom center
    screen.add_widget(_create_widget(
        WidgetType.FUEL_GAUGE, 300, 350, 200, 100,
        name="Fuel", channel_id=RD_CH_FUEL_LEVEL
    ))

    # Gear indicator
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 360, 230, 80, 100,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=48
    ))

    return ScreenTemplate(
        id="street_classic",
        name="Street Classic",
        description="Classic dashboard with RPM, Speed, Coolant temp and Fuel gauge",
        category=TemplateCategory.STREET,
        screens=[screen]
    )


def create_street_modern_template() -> ScreenTemplate:
    """Modern street dashboard with digital displays."""
    screen = ScreenLayout(id=0, name="Main", width=800, height=480)

    # Digital speedometer - large center
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 250, 50, 300, 150,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=72, show_units=True
    ))

    # RPM bar at top
    screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 50, 10, 700, 30,
        name="RPM Bar", channel_id=RD_CH_ENGINE_RPM,
        max_value=8000, color_fg="#00ff00", color_warning="#ffff00", color_danger="#ff0000"
    ))

    # Gear display
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 580, 50, 100, 100,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=64
    ))

    # Bottom row - small gauges
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 50, 280, 150, 80,
        name="Coolant", channel_id=RD_CH_COOLANT_TEMP,
        decimals=0, show_units=True, show_label=True
    ))

    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 220, 280, 150, 80,
        name="Oil Temp", channel_id=RD_CH_OIL_TEMP,
        decimals=0, show_units=True, show_label=True
    ))

    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 430, 280, 150, 80,
        name="Oil Press", channel_id=RD_CH_OIL_PRESSURE,
        decimals=1, show_units=True, show_label=True
    ))

    screen.add_widget(_create_widget(
        WidgetType.FUEL_GAUGE, 600, 280, 150, 80,
        name="Fuel", channel_id=RD_CH_FUEL_LEVEL
    ))

    # Throttle/Brake bars
    screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 50, 400, 340, 30,
        name="Throttle", channel_id=RD_CH_THROTTLE_POSITION,
        color_fg="#00ff00"
    ))

    screen.add_widget(_create_widget(
        WidgetType.BRAKE_BAR, 410, 400, 340, 30,
        name="Brake", channel_id=RD_CH_BRAKE_PRESSURE,
        color_fg="#ff0000"
    ))

    return ScreenTemplate(
        id="street_modern",
        name="Street Modern",
        description="Modern digital dashboard with bar graphs and numeric displays",
        category=TemplateCategory.STREET,
        screens=[screen]
    )


# =============================================================================
# Track/Race Templates
# =============================================================================

def create_track_race_template() -> ScreenTemplate:
    """Track-focused dashboard with lap timer and delta."""
    main_screen = ScreenLayout(id=0, name="Race", width=800, height=480)

    # Delta display - large at top
    main_screen.add_widget(_create_widget(
        WidgetType.DELTA_DISPLAY, 200, 30, 400, 120,
        name="Delta", channel_id=RD_CH_LAP_DELTA
    ))

    # Current lap time
    main_screen.add_widget(_create_widget(
        WidgetType.LAP_TIMER, 250, 170, 300, 80,
        name="Lap Time"
    ))

    # Best lap time
    main_screen.add_widget(_create_widget(
        WidgetType.BEST_LAP, 50, 170, 180, 60,
        name="Best", channel_id=RD_CH_LAP_BEST_TIME
    ))

    # Lap number
    main_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 600, 170, 150, 60,
        name="Lap", channel_id=RD_CH_LAP_NUMBER,
        decimals=0, show_label=True
    ))

    # Sector times
    main_screen.add_widget(_create_widget(
        WidgetType.SECTOR_TIMES, 50, 270, 700, 50,
        name="Sectors"
    ))

    # RPM bar
    main_screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 50, 340, 700, 25,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=9000
    ))

    # Speed
    main_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 50, 390, 150, 70,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=36, show_units=True
    ))

    # Gear
    main_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 220, 390, 100, 70,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=48
    ))

    # G-meter
    main_screen.add_widget(_create_widget(
        WidgetType.G_FORCE_METER, 550, 370, 120, 100,
        name="G-Force"
    ))

    # Temps - small
    main_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 350, 400, 80, 50,
        name="Water", channel_id=RD_CH_COOLANT_TEMP,
        decimals=0, show_label=True
    ))

    main_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 450, 400, 80, 50,
        name="Oil", channel_id=RD_CH_OIL_TEMP,
        decimals=0, show_label=True
    ))

    # Secondary screen - telemetry
    telemetry_screen = ScreenLayout(id=1, name="Telemetry", width=800, height=480)

    telemetry_screen.add_widget(_create_widget(
        WidgetType.G_FORCE_METER, 50, 50, 250, 250,
        name="G-Force"
    ))

    telemetry_screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 350, 50, 400, 40,
        name="Throttle", channel_id=RD_CH_THROTTLE_POSITION,
        color_fg="#00ff00"
    ))

    telemetry_screen.add_widget(_create_widget(
        WidgetType.BRAKE_BAR, 350, 110, 400, 40,
        name="Brake", channel_id=RD_CH_BRAKE_PRESSURE,
        color_fg="#ff0000"
    ))

    telemetry_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 350, 180, 180, 80,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=48
    ))

    telemetry_screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 550, 180, 200, 80,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        decimals=0, font_size=36
    ))

    return ScreenTemplate(
        id="track_race",
        name="Track Race",
        description="Race-focused dashboard with lap timer, delta, and telemetry",
        category=TemplateCategory.TRACK,
        screens=[main_screen, telemetry_screen]
    )


def create_track_endurance_template() -> ScreenTemplate:
    """Endurance racing - focus on engine health."""
    screen = ScreenLayout(id=0, name="Endurance", width=800, height=480)

    # Lap timer top
    screen.add_widget(_create_widget(
        WidgetType.LAP_TIMER, 250, 20, 300, 70,
        name="Lap Time"
    ))

    # Delta
    screen.add_widget(_create_widget(
        WidgetType.DELTA_DISPLAY, 580, 20, 180, 70,
        name="Delta", channel_id=RD_CH_LAP_DELTA
    ))

    # Lap number
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 50, 20, 150, 70,
        name="Lap", channel_id=RD_CH_LAP_NUMBER,
        decimals=0, font_size=36, show_label=True
    ))

    # Temperature gauges - large, center focus
    screen.add_widget(_create_widget(
        WidgetType.TEMP_GAUGE, 50, 110, 180, 180,
        name="Coolant", channel_id=RD_CH_COOLANT_TEMP,
        min_value=60, max_value=120, warning_high=100, danger_high=110
    ))

    screen.add_widget(_create_widget(
        WidgetType.TEMP_GAUGE, 250, 110, 180, 180,
        name="Oil Temp", channel_id=RD_CH_OIL_TEMP,
        min_value=60, max_value=150, warning_high=130, danger_high=140
    ))

    screen.add_widget(_create_widget(
        WidgetType.PRESSURE_GAUGE, 450, 110, 180, 180,
        name="Oil Press", channel_id=RD_CH_OIL_PRESSURE,
        min_value=0, max_value=10, warning_low=2.0, danger_low=1.0
    ))

    screen.add_widget(_create_widget(
        WidgetType.FUEL_GAUGE, 650, 110, 120, 180,
        name="Fuel", channel_id=RD_CH_FUEL_LEVEL
    ))

    # RPM/Speed at bottom
    screen.add_widget(_create_widget(
        WidgetType.RPM_GAUGE, 50, 310, 200, 150,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=8000
    ))

    screen.add_widget(_create_widget(
        WidgetType.SPEEDOMETER, 270, 310, 200, 150,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED
    ))

    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 490, 340, 100, 100,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=64
    ))

    # AFR
    screen.add_widget(_create_widget(
        WidgetType.AFR_BAR, 620, 320, 150, 40,
        name="AFR", channel_id=RD_CH_AFR,
        min_value=0.7, max_value=1.3, target=1.0
    ))

    return ScreenTemplate(
        id="track_endurance",
        name="Track Endurance",
        description="Endurance racing dashboard - engine monitoring focus",
        category=TemplateCategory.TRACK,
        screens=[screen]
    )


# =============================================================================
# Drag Templates
# =============================================================================

def create_drag_template() -> ScreenTemplate:
    """Drag racing - RPM, speed, reaction time."""
    screen = ScreenLayout(id=0, name="Drag", width=800, height=480)

    # Huge RPM display
    screen.add_widget(_create_widget(
        WidgetType.RPM_GAUGE, 150, 30, 500, 250,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=10000, redline=8500
    ))

    # Shift lights bar at very top
    screen.add_widget(_create_widget(
        WidgetType.LED_INDICATOR, 200, 5, 400, 20,
        name="Shift Light", channel_id=RD_CH_ENGINE_RPM,
        threshold=7500, color_on="#ff0000"
    ))

    # Speed - large
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 50, 300, 250, 150,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=72, show_units=True
    ))

    # Gear - large
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 330, 300, 150, 150,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=96
    ))

    # Boost (if turbo)
    screen.add_widget(_create_widget(
        WidgetType.BOOST_GAUGE, 520, 300, 120, 120,
        name="Boost", channel_id=RD_CH_BOOST_PRESSURE,
        min_value=-1, max_value=2.5
    ))

    # ET/Timer
    screen.add_widget(_create_widget(
        WidgetType.LAP_TIMER, 660, 300, 120, 80,
        name="ET"
    ))

    return ScreenTemplate(
        id="drag",
        name="Drag Racing",
        description="Drag racing dashboard with large RPM and speed displays",
        category=TemplateCategory.DRAG,
        screens=[screen]
    )


# =============================================================================
# Drift Templates
# =============================================================================

def create_drift_template() -> ScreenTemplate:
    """Drift - angle, speed, RPM."""
    screen = ScreenLayout(id=0, name="Drift", width=800, height=480)

    # RPM bar across top
    screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 50, 20, 700, 40,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=9000
    ))

    # Speed - large center
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 250, 80, 300, 150,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=72
    ))

    # Gear left of speed
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 100, 100, 120, 120,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=72
    ))

    # G-meter - large
    screen.add_widget(_create_widget(
        WidgetType.G_FORCE_METER, 300, 250, 200, 200,
        name="G-Force"
    ))

    # Throttle bar
    screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 50, 280, 200, 30,
        name="Throttle", channel_id=RD_CH_THROTTLE_POSITION,
        color_fg="#00ff00"
    ))

    # Brake bar
    screen.add_widget(_create_widget(
        WidgetType.BRAKE_BAR, 50, 330, 200, 30,
        name="Brake", channel_id=RD_CH_BRAKE_PRESSURE,
        color_fg="#ff0000"
    ))

    # Temps bottom
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 550, 280, 100, 60,
        name="Water", channel_id=RD_CH_COOLANT_TEMP,
        decimals=0, show_label=True
    ))

    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 670, 280, 100, 60,
        name="Oil", channel_id=RD_CH_OIL_TEMP,
        decimals=0, show_label=True
    ))

    # Boost
    screen.add_widget(_create_widget(
        WidgetType.BOOST_GAUGE, 580, 360, 100, 100,
        name="Boost", channel_id=RD_CH_BOOST_PRESSURE
    ))

    return ScreenTemplate(
        id="drift",
        name="Drift",
        description="Drift dashboard with G-meter and throttle/brake inputs",
        category=TemplateCategory.DRIFT,
        screens=[screen]
    )


# =============================================================================
# Minimal Templates
# =============================================================================

def create_minimal_template() -> ScreenTemplate:
    """Minimal - just the essentials."""
    screen = ScreenLayout(id=0, name="Minimal", width=800, height=480)

    # Speed - center
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 250, 150, 300, 180,
        name="Speed", channel_id=RD_CH_VEHICLE_SPEED,
        decimals=0, font_size=96
    ))

    # RPM bar
    screen.add_widget(_create_widget(
        WidgetType.THROTTLE_BAR, 100, 50, 600, 30,
        name="RPM", channel_id=RD_CH_ENGINE_RPM,
        max_value=8000
    ))

    # Gear
    screen.add_widget(_create_widget(
        WidgetType.NUMERIC_DISPLAY, 580, 170, 100, 120,
        name="Gear", channel_id=RD_CH_GEAR,
        decimals=0, font_size=64
    ))

    return ScreenTemplate(
        id="minimal",
        name="Minimal",
        description="Clean minimal dashboard - speed, RPM, gear",
        category=TemplateCategory.MINIMAL,
        screens=[screen]
    )


def create_empty_template() -> ScreenTemplate:
    """Empty template for custom builds."""
    screen = ScreenLayout(id=0, name="Screen 1", width=800, height=480)

    return ScreenTemplate(
        id="empty",
        name="Blank Canvas",
        description="Empty screen for custom dashboard creation",
        category=TemplateCategory.CUSTOM,
        screens=[screen]
    )


# =============================================================================
# Template Registry
# =============================================================================

def get_all_templates() -> List[ScreenTemplate]:
    """Get all available templates."""
    return [
        create_street_classic_template(),
        create_street_modern_template(),
        create_track_race_template(),
        create_track_endurance_template(),
        create_drag_template(),
        create_drift_template(),
        create_minimal_template(),
        create_empty_template(),
    ]


def get_templates_by_category() -> Dict[TemplateCategory, List[ScreenTemplate]]:
    """Get templates grouped by category."""
    result: Dict[TemplateCategory, List[ScreenTemplate]] = {}

    for template in get_all_templates():
        if template.category not in result:
            result[template.category] = []
        result[template.category].append(template)

    return result


def get_template_by_id(template_id: str) -> ScreenTemplate | None:
    """Get template by ID."""
    for template in get_all_templates():
        if template.id == template_id:
            return template
    return None
