# Device Controller
"""Qt-based device controller with signals/slots."""

import logging
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from communication.comm_manager import CommManager, ConnectionType
from communication.transport_base import TransportState, TransportInfo
from communication.telemetry import TelemetryPacket

logger = logging.getLogger(__name__)


class DeviceController(QObject):
    """
    Qt-based controller for device communication.
    Wraps CommManager with Qt signals for UI integration.
    """

    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connection_state_changed = pyqtSignal(str)  # state name
    telemetry_received = pyqtSignal(object)  # TelemetryPacket
    device_info_received = pyqtSignal(dict)
    config_received = pyqtSignal(bytes)
    config_sent = pyqtSignal(bool)  # success
    error_occurred = pyqtSignal(str)
    log_received = pyqtSignal(int, str)  # level, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._comm = CommManager()
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """Setup callbacks from CommManager."""
        self._comm.add_state_callback(self._on_state_changed)
        self._comm.add_telemetry_callback(self._on_telemetry)
        self._comm.add_error_callback(self._on_error)
        self._comm.add_log_callback(self._on_log)

    def _on_state_changed(self, state: TransportState) -> None:
        """Handle connection state changes."""
        self.connection_state_changed.emit(state.name)

        if state == TransportState.CONNECTED:
            self.connected.emit()
            self.device_info_received.emit(self._comm.device_info)
        elif state == TransportState.DISCONNECTED:
            self.disconnected.emit()

    def _on_telemetry(self, packet: TelemetryPacket) -> None:
        """Handle telemetry data."""
        self.telemetry_received.emit(packet)

    def _on_error(self, message: str) -> None:
        """Handle errors."""
        self.error_occurred.emit(message)

    def _on_log(self, level: int, message: str) -> None:
        """Handle device log messages."""
        self.log_received.emit(level, message)

    @property
    def is_connected(self) -> bool:
        """Check if connected to device."""
        return self._comm.is_connected

    @property
    def connection_type(self) -> Optional[ConnectionType]:
        """Get current connection type."""
        return self._comm.connection_type

    @property
    def device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self._comm.device_info

    @staticmethod
    def list_serial_ports() -> list:
        """List available serial ports."""
        return CommManager.list_serial_ports()

    @staticmethod
    def list_all_connections() -> list:
        """List all available connections."""
        return CommManager.list_all_connections()

    def connect_serial(self, port: str = None, baudrate: int = 115200) -> bool:
        """
        Connect to device via serial port.

        Args:
            port: Serial port name (auto-detect if None)
            baudrate: Baud rate

        Returns:
            True if successful
        """
        logger.info(f"Connecting to serial port: {port or 'auto'}")
        return self._comm.connect_serial(port, baudrate)

    def connect_emulator(self) -> bool:
        """
        Connect to emulator.

        Returns:
            True if successful
        """
        logger.info("Connecting to emulator")
        return self._comm.connect_emulator()

    def disconnect(self) -> None:
        """Disconnect from device."""
        logger.info("Disconnecting from device")
        self._comm.disconnect()

    def ping(self) -> float:
        """
        Ping the device.

        Returns:
            Round-trip time in ms, or -1 on failure
        """
        return self._comm.ping()

    def read_configuration(self) -> Optional[bytes]:
        """
        Read configuration from device.

        Returns:
            Configuration data or None on failure
        """
        logger.info("Reading configuration from device")
        config_data = self._comm.get_configuration()

        if config_data:
            self.config_received.emit(config_data)

        return config_data

    def write_configuration(self, config_data: bytes) -> bool:
        """
        Write configuration to device.

        Args:
            config_data: Configuration data (JSON bytes)

        Returns:
            True if successful
        """
        logger.info("Writing configuration to device")
        success = self._comm.set_configuration(config_data)
        self.config_sent.emit(success)
        return success

    def subscribe_telemetry(self, rate_hz: int = 50) -> bool:
        """
        Subscribe to telemetry streaming.

        Args:
            rate_hz: Telemetry rate in Hz

        Returns:
            True if successful
        """
        logger.info(f"Subscribing to telemetry at {rate_hz} Hz")
        return self._comm.subscribe_telemetry(rate_hz)

    def unsubscribe_telemetry(self) -> bool:
        """
        Unsubscribe from telemetry.

        Returns:
            True if successful
        """
        logger.info("Unsubscribing from telemetry")
        return self._comm.unsubscribe_telemetry()

    def set_channel(self, channel_id: int, value: int) -> bool:
        """
        Set a channel value.

        Args:
            channel_id: Channel ID
            value: New value

        Returns:
            True if successful
        """
        return self._comm.set_channel(channel_id, value)

    def save_to_flash(self) -> bool:
        """
        Save configuration to flash.

        Returns:
            True if successful
        """
        logger.info("Saving configuration to flash")
        return self._comm.save_to_flash()

    def restart_device(self) -> bool:
        """
        Restart the device.

        Returns:
            True if command sent
        """
        logger.info("Restarting device")
        return self._comm.restart_device()
