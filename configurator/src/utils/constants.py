# Constants
"""Application constants for Racing Dashboard Configurator."""

# Application info
APP_NAME = "Racing Dashboard Configurator"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Racing Dashboard Team"
ORGANIZATION = "RacingDashboard"

# Config file
CONFIG_VERSION = "1.0"
CONFIG_EXTENSION = ".rdconfig"
DEFAULT_CONFIG_NAME = "untitled"

# Display profiles
DISPLAY_PROFILES = {
    "1024x600": {"width": 1024, "height": 600, "name": "Standard 7\""},
    "1280x480": {"width": 1280, "height": 480, "name": "Ultrawide"},
    "800x480": {"width": 800, "height": 480, "name": "Compact 5\""},
    "480x320": {"width": 480, "height": 320, "name": "Minimal 3.5\""},
}

# Grid settings
DEFAULT_GRID_COLUMNS = 24
DEFAULT_GRID_ROWS = 12
DEFAULT_GUTTER_SIZE = 4

# Communication
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1.0
WEBSOCKET_PORT = 81
PROTOCOL_HEADER = 0xAA
PROTOCOL_FOOTER = 0x55
MAX_PAYLOAD_SIZE = 4096

# Telemetry
TELEMETRY_DEFAULT_RATE_HZ = 50
TELEMETRY_MAX_RATE_HZ = 100

# UI
MIN_WINDOW_WIDTH = 1280
MIN_WINDOW_HEIGHT = 800
DOCK_MIN_WIDTH = 250
PROPERTY_PANEL_WIDTH = 300

# Theme presets
THEME_PRESETS = [
    "Motec Dark",
    "AIM Sport Light",
    "Rally High-Contrast",
    "Night Mode",
    "Endurance",
]

# Widget types
WIDGET_CATEGORIES = {
    "Gauges": ["rpm_gauge", "speedometer", "temp_gauge", "fuel_gauge", "pressure_gauge"],
    "Indicators": ["gear_indicator", "shift_lights", "status_pill", "warning_light"],
    "Meters": ["g_force_meter", "throttle_bar", "brake_bar"],
    "Timers": ["lap_timer", "delta_display", "sector_times"],
    "Text": ["custom_text", "variable_display"],
}

# Max limits
MAX_SCREENS = 10
MAX_WIDGETS_PER_SCREEN = 64
MAX_CAN_SIGNALS = 256
