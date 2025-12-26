# Configuration Exporter
"""Export dashboard configuration for device firmware."""

import json
import struct
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from models.dashboard_config import DashboardConfig
from models.screen_layout import ScreenLayout, WidgetConfig
from models.widget_types import WidgetType


@dataclass
class ExportResult:
    """Result of export operation."""
    success: bool
    file_path: str = ""
    file_size: int = 0
    checksum: str = ""
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """Validates configuration before export."""

    def __init__(self, config: DashboardConfig):
        self._config = config
        self._errors: List[str] = []
        self._warnings: List[str] = []

    @property
    def errors(self) -> List[str]:
        return self._errors

    @property
    def warnings(self) -> List[str]:
        return self._warnings

    def validate(self) -> bool:
        """Run all validations. Returns True if no critical errors."""
        self._errors.clear()
        self._warnings.clear()

        self._validate_display()
        self._validate_can()
        self._validate_screens()
        self._validate_widgets()

        return len(self._errors) == 0

    def _validate_display(self) -> None:
        """Validate display settings."""
        display = self._config.display

        # Check resolution
        valid_resolutions = [
            (1024, 600), (800, 480), (480, 320),
            (1280, 720), (1920, 1080)
        ]
        if (display.width, display.height) not in valid_resolutions:
            self._warnings.append(
                f"Non-standard resolution: {display.width}x{display.height}"
            )

        # Check brightness
        if display.brightness_max < 100 or display.brightness_max > 1000:
            self._warnings.append(
                f"Unusual brightness value: {display.brightness_max}"
            )

        # Check refresh rate
        if display.refresh_rate not in [30, 60, 120]:
            self._warnings.append(
                f"Non-standard refresh rate: {display.refresh_rate}Hz"
            )

    def _validate_can(self) -> None:
        """Validate CAN settings."""
        can = self._config.can

        # Check baudrate
        valid_baudrates = [125000, 250000, 500000, 1000000]
        if can.baudrate not in valid_baudrates:
            self._errors.append(
                f"Invalid CAN baudrate: {can.baudrate}. "
                f"Valid: {valid_baudrates}"
            )

        # Check FD baudrate
        if can.fd_enabled:
            valid_fd_rates = [2000000, 5000000, 8000000]
            if can.fd_baudrate not in valid_fd_rates:
                self._warnings.append(
                    f"Non-standard CAN FD baudrate: {can.fd_baudrate}"
                )

    def _validate_screens(self) -> None:
        """Validate screen layouts."""
        if not self._config.screens:
            self._errors.append("No screens defined")
            return

        if len(self._config.screens) > 10:
            self._errors.append(
                f"Too many screens: {len(self._config.screens)}. Maximum is 10."
            )

        for i, screen in enumerate(self._config.screens):
            if not screen.widgets:
                self._warnings.append(f"Screen {i+1} '{screen.name}' has no widgets")

    def _validate_widgets(self) -> None:
        """Validate widget configurations."""
        for screen in self._config.screens:
            for widget in screen.widgets:
                # Check bounds
                if widget.x < 0 or widget.y < 0:
                    self._errors.append(
                        f"Widget '{widget.name}' has negative position"
                    )

                if widget.x + widget.width > screen.width:
                    self._warnings.append(
                        f"Widget '{widget.name}' extends beyond screen width"
                    )

                if widget.y + widget.height > screen.height:
                    self._warnings.append(
                        f"Widget '{widget.name}' extends beyond screen height"
                    )

                # Check size
                if widget.width < 20 or widget.height < 20:
                    self._warnings.append(
                        f"Widget '{widget.name}' is very small: {widget.width}x{widget.height}"
                    )


class ConfigExporter:
    """Exports configuration for device firmware."""

    # Widget type to firmware ID mapping
    WIDGET_TYPE_IDS = {
        WidgetType.RPM_GAUGE: 1,
        WidgetType.SPEEDOMETER: 2,
        WidgetType.GEAR_INDICATOR: 3,
        WidgetType.SHIFT_LIGHTS: 4,
        WidgetType.TEMP_GAUGE: 5,
        WidgetType.FUEL_GAUGE: 6,
        WidgetType.G_FORCE_METER: 7,
        WidgetType.LAP_TIMER: 8,
        WidgetType.VARIABLE_DISPLAY: 9,
        WidgetType.STATUS_PILL: 10,
        WidgetType.CUSTOM_TEXT: 11,
        WidgetType.LINE_GRAPH: 12,
        WidgetType.BAR_CHART: 13,
        WidgetType.HISTOGRAM: 14,
        WidgetType.PIE_CHART: 15,
    }

    def __init__(self, config: DashboardConfig):
        self._config = config
        self._validator = ConfigValidator(config)

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration before export."""
        is_valid = self._validator.validate()
        return is_valid, self._validator.errors, self._validator.warnings

    def export_json(self, file_path: str, compact: bool = True) -> ExportResult:
        """Export configuration as JSON for device."""
        result = ExportResult(success=False)

        # Validate first
        is_valid = self._validator.validate()
        result.errors = self._validator.errors.copy()
        result.warnings = self._validator.warnings.copy()

        if not is_valid:
            return result

        try:
            # Build device config
            device_config = self._build_device_config()

            # Serialize
            if compact:
                json_str = json.dumps(device_config, separators=(',', ':'))
            else:
                json_str = json.dumps(device_config, indent=2)

            # Write file
            path = Path(file_path)
            path.write_text(json_str, encoding='utf-8')

            # Calculate checksum
            checksum = hashlib.md5(json_str.encode()).hexdigest()

            result.success = True
            result.file_path = str(path.absolute())
            result.file_size = len(json_str)
            result.checksum = checksum

        except Exception as e:
            result.errors.append(f"Export failed: {str(e)}")

        return result

    def export_binary(self, file_path: str) -> ExportResult:
        """Export configuration as binary format for device."""
        result = ExportResult(success=False)

        # Validate first
        is_valid = self._validator.validate()
        result.errors = self._validator.errors.copy()
        result.warnings = self._validator.warnings.copy()

        if not is_valid:
            return result

        try:
            # Build binary data
            data = self._build_binary_config()

            # Write file
            path = Path(file_path)
            path.write_bytes(data)

            # Calculate checksum
            checksum = hashlib.md5(data).hexdigest()

            result.success = True
            result.file_path = str(path.absolute())
            result.file_size = len(data)
            result.checksum = checksum

        except Exception as e:
            result.errors.append(f"Binary export failed: {str(e)}")

        return result

    def _build_device_config(self) -> Dict[str, Any]:
        """Build optimized device configuration dictionary."""
        cfg = self._config

        return {
            "v": 1,  # Config version
            "ts": int(datetime.now().timestamp()),  # Timestamp
            "d": {  # Display
                "w": cfg.display.width,
                "h": cfg.display.height,
                "o": self._orientation_to_int(cfg.display.orientation),
                "b": cfg.display.brightness_max,
                "ab": 1 if cfg.display.auto_brightness else 0,
                "r": cfg.display.refresh_rate,
            },
            "t": {  # Theme
                "p": cfg.theme.active_preset,
                "an": 1 if cfg.theme.auto_night_mode else 0,
                "ns": cfg.theme.night_mode_start,
                "ne": cfg.theme.night_mode_end,
            },
            "c": {  # CAN
                "e": 1 if cfg.can.enabled else 0,
                "br": cfg.can.baudrate,
                "fd": 1 if cfg.can.fd_enabled else 0,
                "fdr": cfg.can.fd_baudrate,
            },
            "cs": {  # CAN Security
                "m": self._security_mode_to_int(cfg.can_security.mode),
                "rp": 1 if cfg.can_security.replay_protection else 0,
                "id": 1 if cfg.can_security.intrusion_detection else 0,
            },
            "g": {  # GPS
                "e": 1 if cfg.gps.enabled else 0,
                "ur": cfg.gps.update_rate,
                "at": 1 if cfg.gps.auto_track_detection else 0,
            },
            "cam": {  # Camera
                "e": 1 if cfg.camera.enabled else 0,
                "t": self._camera_type_to_int(cfg.camera.camera_type),
                "ar": 1 if cfg.camera.auto_record else 0,
            },
            "cl": {  # Cloud
                "e": 1 if cfg.cloud.enabled else 0,
                "rt": 1 if cfg.cloud.real_time_streaming else 0,
                "au": 1 if cfg.cloud.auto_upload_sessions else 0,
            },
            "va": {  # Voice Alerts
                "e": 1 if cfg.voice.enabled else 0,
                "vol": cfg.voice.volume,
            },
            "l": {  # Logger
                "e": 1 if cfg.logger.enabled else 0,
                "sr": cfg.logger.sample_rate,
                "cl": cfg.logger.compression_level,
            },
            "lt": {  # Lap Timer
                "e": 1 if cfg.lap_timer.enabled else 0,
                "ad": 1 if cfg.lap_timer.auto_detection else 0,
            },
            "ota": {  # OTA
                "e": 1 if cfg.ota.enabled else 0,
                "ac": 1 if cfg.ota.auto_check else 0,
                "ab": 1 if cfg.ota.allow_beta else 0,
            },
            "w": {  # WiFi
                "ae": 1 if cfg.wifi.ap_enabled else 0,
                "as": cfg.wifi.ap_ssid,
                "ac": cfg.wifi.ap_channel,
            },
            "s": [self._build_screen_config(s) for s in cfg.screens],  # Screens
            "si": cfg.active_screen_index,  # Active screen index
        }

    def _build_screen_config(self, screen: ScreenLayout) -> Dict[str, Any]:
        """Build screen configuration."""
        return {
            "n": screen.name,
            "w": screen.width,
            "h": screen.height,
            "bg": screen.background_color,
            "ws": [self._build_widget_config(w) for w in screen.widgets],
        }

    def _build_widget_config(self, widget: WidgetConfig) -> Dict[str, Any]:
        """Build widget configuration."""
        config = {
            "t": self.WIDGET_TYPE_IDS.get(widget.widget_type, 0),
            "x": widget.x,
            "y": widget.y,
            "w": widget.width,
            "h": widget.height,
            "z": widget.z_index,
        }

        # Add properties if present
        if widget.properties:
            config["p"] = widget.properties

        # Add channel bindings if present
        if widget.channel_bindings:
            config["ch"] = widget.channel_bindings

        return config

    def _build_binary_config(self) -> bytes:
        """Build binary configuration for device."""
        parts = []

        # Header (magic + version + timestamp)
        parts.append(struct.pack('<4sII',
                                 b'RDCF',  # Magic: Racing Dashboard Config
                                 1,  # Version
                                 int(datetime.now().timestamp())))

        # Display settings
        d = self._config.display
        parts.append(struct.pack('<HHBBHB',
                                 d.width, d.height,
                                 self._orientation_to_int(d.orientation),
                                 1 if d.auto_brightness else 0,
                                 d.brightness_max,
                                 d.refresh_rate))

        # CAN settings
        c = self._config.can
        parts.append(struct.pack('<BIBI',
                                 1 if c.enabled else 0,
                                 c.baudrate,
                                 1 if c.fd_enabled else 0,
                                 c.fd_baudrate))

        # GPS settings
        g = self._config.gps
        parts.append(struct.pack('<BBB',
                                 1 if g.enabled else 0,
                                 g.update_rate,
                                 1 if g.auto_track_detection else 0))

        # Number of screens
        parts.append(struct.pack('<B', len(self._config.screens)))

        # Screen data
        for screen in self._config.screens:
            # Screen header
            name_bytes = screen.name.encode('utf-8')[:31]
            name_padded = name_bytes.ljust(32, b'\x00')
            parts.append(name_padded)
            parts.append(struct.pack('<HHH',
                                     screen.width, screen.height,
                                     len(screen.widgets)))

            # Widgets
            for widget in screen.widgets:
                parts.append(struct.pack('<BHHHHH',
                                         self.WIDGET_TYPE_IDS.get(widget.widget_type, 0),
                                         widget.x, widget.y,
                                         widget.width, widget.height,
                                         widget.z_index))

        # Calculate checksum
        data = b''.join(parts)
        checksum = hashlib.crc32(data) & 0xFFFFFFFF

        # Append checksum and length
        return data + struct.pack('<II', checksum, len(data))

    @staticmethod
    def _orientation_to_int(orientation: str) -> int:
        """Convert orientation string to integer."""
        mapping = {
            "landscape": 0,
            "portrait": 1,
            "landscape_inv": 2,
            "portrait_inv": 3,
        }
        return mapping.get(orientation, 0)

    @staticmethod
    def _security_mode_to_int(mode: str) -> int:
        """Convert security mode to integer."""
        mapping = {
            "disabled": 0,
            "mac_only": 1,
            "encrypt_mac": 2,
            "encrypt_sign": 3,
        }
        return mapping.get(mode, 0)

    @staticmethod
    def _camera_type_to_int(camera_type: str) -> int:
        """Convert camera type to integer."""
        mapping = {
            "gopro_wifi": 0,
            "insta360_wifi": 1,
            "rtsp": 2,
        }
        return mapping.get(camera_type, 0)


def export_for_device(config: DashboardConfig, file_path: str,
                      format: str = "json") -> ExportResult:
    """
    Export configuration for device.

    Args:
        config: Dashboard configuration
        file_path: Output file path
        format: "json" or "binary"

    Returns:
        ExportResult with status and details
    """
    exporter = ConfigExporter(config)

    if format == "binary":
        return exporter.export_binary(file_path)
    else:
        return exporter.export_json(file_path)
