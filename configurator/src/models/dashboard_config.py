# Dashboard Configuration Model
"""Main configuration model for Racing Dashboard device."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .screen_layout import ScreenLayout, create_default_screen


@dataclass
class DisplaySettings:
    """Display hardware settings."""
    profile: str = "1024x600"
    width: int = 1024
    height: int = 600
    orientation: str = "landscape"  # landscape, portrait, landscape_inv, portrait_inv
    brightness_max: int = 700
    auto_brightness: bool = True
    refresh_rate: int = 60


@dataclass
class ThemeSettings:
    """Theme configuration."""
    active_preset: str = "Motec Dark"
    auto_night_mode: bool = True
    night_mode_start: int = 20  # hour
    night_mode_end: int = 6  # hour
    day_theme: str = "Motec Dark"
    night_theme: str = "Night Mode"
    brightness_multiplier: float = 1.0


@dataclass
class CANSettings:
    """CAN bus configuration."""
    enabled: bool = True
    baudrate: int = 500000
    fd_enabled: bool = False
    fd_baudrate: int = 5000000


@dataclass
class CANSecuritySettings:
    """CAN security configuration."""
    mode: str = "disabled"  # disabled, mac_only, encrypt_mac, encrypt_sign
    replay_protection: bool = True
    intrusion_detection: bool = True
    key_rotation_interval: int = 3600  # seconds


@dataclass
class GPSSettings:
    """GPS configuration."""
    enabled: bool = True
    update_rate: int = 25  # Hz
    auto_track_detection: bool = True


@dataclass
class CameraSettings:
    """Camera integration settings."""
    enabled: bool = False
    camera_type: str = "gopro_wifi"  # gopro_wifi, insta360_wifi, rtsp
    ip_address: str = ""
    auto_record: bool = True
    trigger_mode: str = "ignition"  # manual, ignition, speed, lap_start


@dataclass
class CloudSettings:
    """Cloud telemetry settings."""
    enabled: bool = False
    provider: str = "aws_iot"  # aws_iot, azure_iot, google_iot, custom
    endpoint: str = ""
    device_id: str = ""
    real_time_streaming: bool = True
    auto_upload_sessions: bool = True


@dataclass
class VoiceSettings:
    """Voice alerts settings."""
    enabled: bool = True
    engine: str = "espeak"  # google_tts, espeak, flite, prerecorded
    language: str = "en_us"
    volume: int = 75
    output: str = "bluetooth"  # bluetooth, speaker, headphone


@dataclass
class LoggerSettings:
    """Data logger settings."""
    enabled: bool = True
    format: str = "compressed"  # csv, binary, compressed, parquet
    sample_rate: int = 100  # Hz
    compression_level: int = 6
    trigger_mode: str = "ignition"
    pre_trigger_duration: int = 10  # seconds


@dataclass
class LapTimerSettings:
    """Lap timer settings."""
    enabled: bool = True
    auto_detection: bool = True
    current_track: str = ""


@dataclass
class OTASettings:
    """OTA update settings."""
    enabled: bool = True
    auto_check: bool = True
    check_interval: int = 24  # hours
    allow_beta: bool = False
    server_url: str = ""


@dataclass
class WiFiSettings:
    """WiFi configuration."""
    ap_enabled: bool = True
    ap_ssid: str = "RacingDashboard"
    ap_password: str = ""
    ap_channel: int = 6


@dataclass
class DashboardConfig:
    """
    Main configuration for Racing Dashboard device.
    Contains all settings organized by module.
    """
    # Metadata
    version: str = "1.0"
    name: str = "Untitled Project"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())

    # Module settings
    display: DisplaySettings = field(default_factory=DisplaySettings)
    theme: ThemeSettings = field(default_factory=ThemeSettings)
    can: CANSettings = field(default_factory=CANSettings)
    can_security: CANSecuritySettings = field(default_factory=CANSecuritySettings)
    gps: GPSSettings = field(default_factory=GPSSettings)
    camera: CameraSettings = field(default_factory=CameraSettings)
    cloud: CloudSettings = field(default_factory=CloudSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    logger: LoggerSettings = field(default_factory=LoggerSettings)
    lap_timer: LapTimerSettings = field(default_factory=LapTimerSettings)
    ota: OTASettings = field(default_factory=OTASettings)
    wifi: WiFiSettings = field(default_factory=WiFiSettings)

    # Screen layouts
    screens: List[ScreenLayout] = field(default_factory=list)
    active_screen_index: int = 0

    def __post_init__(self):
        # Create default screen if none exist
        if not self.screens:
            self.screens.append(create_default_screen())

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "version": self.version,
            "name": self.name,
            "created": self.created,
            "modified": datetime.now().isoformat(),
            "display": self._dataclass_to_dict(self.display),
            "theme": self._dataclass_to_dict(self.theme),
            "can": self._dataclass_to_dict(self.can),
            "can_security": self._dataclass_to_dict(self.can_security),
            "gps": self._dataclass_to_dict(self.gps),
            "camera": self._dataclass_to_dict(self.camera),
            "cloud": self._dataclass_to_dict(self.cloud),
            "voice": self._dataclass_to_dict(self.voice),
            "logger": self._dataclass_to_dict(self.logger),
            "lap_timer": self._dataclass_to_dict(self.lap_timer),
            "ota": self._dataclass_to_dict(self.ota),
            "wifi": self._dataclass_to_dict(self.wifi),
            "screens": [s.to_dict() for s in self.screens],
            "active_screen_index": self.active_screen_index,
        }

    @staticmethod
    def _dataclass_to_dict(obj) -> Dict[str, Any]:
        """Convert a dataclass instance to dictionary."""
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardConfig":
        """Create configuration from dictionary."""
        config = cls()

        # Metadata
        config.version = data.get("version", "1.0")
        config.name = data.get("name", "Untitled Project")
        config.created = data.get("created", datetime.now().isoformat())
        config.modified = data.get("modified", datetime.now().isoformat())

        # Load module settings
        if "display" in data:
            config.display = DisplaySettings(**data["display"])
        if "theme" in data:
            config.theme = ThemeSettings(**data["theme"])
        if "can" in data:
            config.can = CANSettings(**data["can"])
        if "can_security" in data:
            config.can_security = CANSecuritySettings(**data["can_security"])
        if "gps" in data:
            config.gps = GPSSettings(**data["gps"])
        if "camera" in data:
            config.camera = CameraSettings(**data["camera"])
        if "cloud" in data:
            config.cloud = CloudSettings(**data["cloud"])
        if "voice" in data:
            config.voice = VoiceSettings(**data["voice"])
        if "logger" in data:
            config.logger = LoggerSettings(**data["logger"])
        if "lap_timer" in data:
            config.lap_timer = LapTimerSettings(**data["lap_timer"])
        if "ota" in data:
            config.ota = OTASettings(**data["ota"])
        if "wifi" in data:
            config.wifi = WiFiSettings(**data["wifi"])

        # Load screens
        if "screens" in data:
            config.screens = [ScreenLayout.from_dict(s) for s in data["screens"]]

        config.active_screen_index = data.get("active_screen_index", 0)

        return config

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "DashboardConfig":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_screen(self, name: str = "New Screen") -> ScreenLayout:
        """Add a new screen layout."""
        screen = ScreenLayout(name=name, width=self.display.width, height=self.display.height)
        self.screens.append(screen)
        return screen

    def remove_screen(self, index: int) -> bool:
        """Remove a screen layout by index."""
        if 0 <= index < len(self.screens) and len(self.screens) > 1:
            del self.screens[index]
            if self.active_screen_index >= len(self.screens):
                self.active_screen_index = len(self.screens) - 1
            return True
        return False

    def get_active_screen(self) -> Optional[ScreenLayout]:
        """Get the currently active screen."""
        if 0 <= self.active_screen_index < len(self.screens):
            return self.screens[self.active_screen_index]
        return None

    def set_active_screen(self, index: int) -> bool:
        """Set the active screen by index."""
        if 0 <= index < len(self.screens):
            self.active_screen_index = index
            return True
        return False
