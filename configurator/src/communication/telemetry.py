# Telemetry Structures
"""Data structures for telemetry from Racing Dashboard device."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import IntFlag


class FaultFlags(IntFlag):
    """Device fault flags."""
    NONE = 0
    OVER_VOLTAGE = 1 << 0
    UNDER_VOLTAGE = 1 << 1
    OVER_TEMP = 1 << 2
    CAN1_ERROR = 1 << 3
    CAN2_ERROR = 1 << 4
    GPS_ERROR = 1 << 5
    SD_ERROR = 1 << 6
    DISPLAY_ERROR = 1 << 7
    WIFI_ERROR = 1 << 8
    FLASH_ERROR = 1 << 9


@dataclass
class TelemetryPacket:
    """
    Real-time telemetry data from the device.
    """
    # Timestamp
    timestamp_ms: int = 0

    # Engine
    rpm: int = 0
    throttle_percent: int = 0
    brake_percent: int = 0
    gear: int = 0

    # Vehicle
    speed_kmh: int = 0
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0

    # Temperatures
    coolant_temp_c: int = 0
    oil_temp_c: int = 0
    intake_temp_c: int = 0
    exhaust_temp_c: int = 0

    # Pressures
    oil_pressure_psi: float = 0.0
    fuel_pressure_psi: float = 0.0
    boost_pressure_psi: float = 0.0

    # Fuel
    fuel_level_percent: int = 0
    fuel_flow_lph: float = 0.0

    # Electrical
    battery_voltage: float = 0.0

    # GPS
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    gps_speed_kmh: float = 0.0
    gps_heading: float = 0.0
    gps_altitude_m: float = 0.0
    gps_satellites: int = 0

    # Lap timing
    lap_number: int = 0
    lap_time_ms: int = 0
    best_lap_time_ms: int = 0
    delta_ms: int = 0
    sector: int = 0

    # System
    fault_flags: FaultFlags = FaultFlags.NONE
    cpu_load_percent: int = 0

    # Custom channels (CAN signals, etc.)
    custom_channels: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp_ms": self.timestamp_ms,
            "rpm": self.rpm,
            "throttle_percent": self.throttle_percent,
            "brake_percent": self.brake_percent,
            "gear": self.gear,
            "speed_kmh": self.speed_kmh,
            "g_lateral": self.g_lateral,
            "g_longitudinal": self.g_longitudinal,
            "coolant_temp_c": self.coolant_temp_c,
            "oil_temp_c": self.oil_temp_c,
            "intake_temp_c": self.intake_temp_c,
            "exhaust_temp_c": self.exhaust_temp_c,
            "oil_pressure_psi": self.oil_pressure_psi,
            "fuel_pressure_psi": self.fuel_pressure_psi,
            "boost_pressure_psi": self.boost_pressure_psi,
            "fuel_level_percent": self.fuel_level_percent,
            "fuel_flow_lph": self.fuel_flow_lph,
            "battery_voltage": self.battery_voltage,
            "gps_lat": self.gps_lat,
            "gps_lon": self.gps_lon,
            "gps_speed_kmh": self.gps_speed_kmh,
            "gps_heading": self.gps_heading,
            "gps_altitude_m": self.gps_altitude_m,
            "gps_satellites": self.gps_satellites,
            "lap_number": self.lap_number,
            "lap_time_ms": self.lap_time_ms,
            "best_lap_time_ms": self.best_lap_time_ms,
            "delta_ms": self.delta_ms,
            "sector": self.sector,
            "fault_flags": int(self.fault_flags),
            "cpu_load_percent": self.cpu_load_percent,
            "custom_channels": self.custom_channels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetryPacket":
        """Create from dictionary."""
        packet = cls()
        for key, value in data.items():
            if key == "fault_flags":
                packet.fault_flags = FaultFlags(value)
            elif hasattr(packet, key):
                setattr(packet, key, value)
        return packet

    def format_lap_time(self, time_ms: Optional[int] = None) -> str:
        """Format lap time as MM:SS.mmm"""
        if time_ms is None:
            time_ms = self.lap_time_ms

        if time_ms <= 0:
            return "--:--.---"

        minutes = time_ms // 60000
        seconds = (time_ms % 60000) // 1000
        millis = time_ms % 1000

        return f"{minutes:02d}:{seconds:02d}.{millis:03d}"

    def format_delta(self) -> str:
        """Format delta time with sign."""
        if self.delta_ms == 0:
            return "+0.000"

        sign = "+" if self.delta_ms > 0 else "-"
        abs_delta = abs(self.delta_ms)
        seconds = abs_delta // 1000
        millis = abs_delta % 1000

        return f"{sign}{seconds}.{millis:03d}"

    @property
    def has_faults(self) -> bool:
        """Check if any fault flags are set."""
        return self.fault_flags != FaultFlags.NONE

    def get_fault_names(self) -> list:
        """Get list of active fault names."""
        faults = []
        for flag in FaultFlags:
            if flag != FaultFlags.NONE and self.fault_flags & flag:
                faults.append(flag.name)
        return faults


@dataclass
class ConnectionStats:
    """Statistics about the device connection."""
    connected_since_ms: int = 0
    packets_received: int = 0
    packets_sent: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0
    errors: int = 0
    last_ping_ms: float = 0.0
    avg_latency_ms: float = 0.0

    def reset(self) -> None:
        """Reset all statistics."""
        self.connected_since_ms = 0
        self.packets_received = 0
        self.packets_sent = 0
        self.bytes_received = 0
        self.bytes_sent = 0
        self.errors = 0
        self.last_ping_ms = 0.0
        self.avg_latency_ms = 0.0
