# Widgets package
"""Custom widgets for Racing Dashboard Configurator."""

from .monitor_panel import (
    MonitorPanel,
    CANMonitorWidget,
    TelemetryWidget,
    GPSWidget,
    LogWidget,
    TelemetryItem,
)

__all__ = [
    "MonitorPanel",
    "CANMonitorWidget",
    "TelemetryWidget",
    "GPSWidget",
    "LogWidget",
    "TelemetryItem",
]
