# Communication Manager
"""High-level communication manager for device connectivity."""

import logging
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from enum import Enum, auto

from .transport_base import TransportBase, TransportState, TransportInfo
from .serial_transport import SerialTransport
from .emulator_transport import EmulatorTransport
from .protocol import Protocol, ProtocolFrame, MessageType, ErrorCode
from .telemetry import TelemetryPacket, ConnectionStats

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Connection type enumeration."""
    SERIAL = auto()
    WIFI = auto()
    EMULATOR = auto()


class CommManager:
    """
    High-level communication manager.
    Handles device discovery, connection, and data exchange.
    """

    def __init__(self):
        self._transport: Optional[TransportBase] = None
        self._protocol = Protocol()
        self._connection_type: Optional[ConnectionType] = None

        # Callbacks
        self._state_callbacks: List[Callable[[TransportState], None]] = []
        self._telemetry_callbacks: List[Callable[[TelemetryPacket], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
        self._log_callbacks: List[Callable[[int, str], None]] = []

        # Device info
        self._device_info: Dict[str, Any] = {}

        # Statistics
        self._stats = ConnectionStats()

        # Threading
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

        # Pending responses
        self._pending_response: Optional[ProtocolFrame] = None
        self._response_event = threading.Event()

    @property
    def is_connected(self) -> bool:
        """Check if connected to a device."""
        return self._transport is not None and self._transport.is_connected

    @property
    def connection_type(self) -> Optional[ConnectionType]:
        """Get current connection type."""
        return self._connection_type

    @property
    def device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self._device_info.copy()

    @property
    def stats(self) -> ConnectionStats:
        """Get connection statistics."""
        return self._stats

    def add_state_callback(self, callback: Callable[[TransportState], None]) -> None:
        """Add callback for connection state changes."""
        self._state_callbacks.append(callback)

    def add_telemetry_callback(self, callback: Callable[[TelemetryPacket], None]) -> None:
        """Add callback for telemetry data."""
        self._telemetry_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for errors."""
        self._error_callbacks.append(callback)

    def add_log_callback(self, callback: Callable[[int, str], None]) -> None:
        """Add callback for device log messages."""
        self._log_callbacks.append(callback)

    @staticmethod
    def list_serial_ports() -> List[TransportInfo]:
        """List available serial ports."""
        return SerialTransport.list_ports()

    @staticmethod
    def list_all_connections() -> List[TransportInfo]:
        """List all available connections (serial + emulator)."""
        connections = SerialTransport.list_ports()
        connections.extend(EmulatorTransport.list_ports())
        return connections

    def connect_serial(self, port: str = None, baudrate: int = 115200) -> bool:
        """
        Connect to a device via serial port.

        Args:
            port: Serial port name (auto-detect if None)
            baudrate: Baud rate

        Returns:
            True if connection successful
        """
        if self.is_connected:
            self.disconnect()

        self._transport = SerialTransport()
        self._setup_transport_callbacks()

        if self._transport.connect(port=port, baudrate=baudrate):
            self._connection_type = ConnectionType.SERIAL
            self._start_receive_thread()
            self._fetch_device_info()
            return True

        self._transport = None
        return False

    def connect_emulator(self) -> bool:
        """
        Connect to the emulator for development.

        Returns:
            True if connection successful
        """
        if self.is_connected:
            self.disconnect()

        self._transport = EmulatorTransport()
        self._setup_transport_callbacks()

        if self._transport.connect():
            self._connection_type = ConnectionType.EMULATOR
            self._start_receive_thread()
            self._fetch_device_info()
            return True

        self._transport = None
        return False

    def disconnect(self) -> None:
        """Disconnect from the device."""
        if not self._transport:
            return

        logger.info("Disconnecting from device")

        # Stop receive thread
        self._running = False
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=1.0)

        # Disconnect transport
        self._transport.disconnect()
        self._transport = None
        self._connection_type = None
        self._device_info.clear()
        self._stats.reset()

    def _setup_transport_callbacks(self) -> None:
        """Setup callbacks on the transport."""
        if self._transport:
            self._transport.set_state_callback(self._on_state_changed)
            self._transport.set_error_callback(self._on_error)

    def _on_state_changed(self, state: TransportState) -> None:
        """Handle transport state changes."""
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")

    def _on_error(self, message: str) -> None:
        """Handle transport errors."""
        self._stats.errors += 1
        for callback in self._error_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error callback error: {e}")

    def _start_receive_thread(self) -> None:
        """Start background receive thread."""
        self._running = True
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()

    def _receive_loop(self) -> None:
        """Background thread for receiving and processing data."""
        while self._running and self._transport:
            try:
                data = self._transport.receive(timeout=0.1)
                if data:
                    self._stats.bytes_received += len(data)
                    self._process_received_data(data)
            except Exception as e:
                if self._running:
                    logger.error(f"Receive error: {e}")
                    self._on_error(str(e))

    def _process_received_data(self, data: bytes) -> None:
        """Process received data and dispatch frames."""
        frames = self._protocol.feed_data(data)

        for frame in frames:
            self._stats.packets_received += 1
            self._handle_frame(frame)

    def _handle_frame(self, frame: ProtocolFrame) -> None:
        """Handle a received protocol frame."""
        if frame.message_type == MessageType.TELEMETRY_DATA:
            # Parse and dispatch telemetry
            telemetry_data = self._protocol.parse_telemetry(frame.payload)
            packet = TelemetryPacket.from_dict(telemetry_data)
            self._dispatch_telemetry(packet)

        elif frame.message_type == MessageType.LOG_MESSAGE:
            # Parse and dispatch log message
            if len(frame.payload) > 1:
                level = frame.payload[0]
                message = frame.payload[1:].decode('utf-8', errors='ignore')
                for callback in self._log_callbacks:
                    try:
                        callback(level, message)
                    except Exception as e:
                        logger.error(f"Log callback error: {e}")

        elif frame.message_type == MessageType.ERROR:
            # Parse error
            error_code, message = self._protocol.parse_error(frame.payload)
            self._on_error(f"Device error {error_code.name}: {message}")

        else:
            # Signal pending response
            with self._lock:
                self._pending_response = frame
                self._response_event.set()

    def _dispatch_telemetry(self, packet: TelemetryPacket) -> None:
        """Dispatch telemetry to callbacks."""
        for callback in self._telemetry_callbacks:
            try:
                callback(packet)
            except Exception as e:
                logger.error(f"Telemetry callback error: {e}")

    def _send_and_wait(self, data: bytes, expected_type: MessageType,
                       timeout: float = 2.0) -> Optional[ProtocolFrame]:
        """
        Send data and wait for response.

        Args:
            data: Data to send
            expected_type: Expected response message type
            timeout: Response timeout

        Returns:
            Response frame or None on timeout
        """
        if not self._transport:
            return None

        with self._lock:
            self._pending_response = None
            self._response_event.clear()

        if not self._transport.send(data):
            return None

        self._stats.packets_sent += 1
        self._stats.bytes_sent += len(data)

        # Wait for response
        if self._response_event.wait(timeout):
            with self._lock:
                response = self._pending_response
                self._pending_response = None
                return response

        return None

    def _fetch_device_info(self) -> bool:
        """Fetch device information."""
        data = self._protocol.create_get_info()
        response = self._send_and_wait(data, MessageType.INFO_RESPONSE)

        if response and response.message_type == MessageType.INFO_RESPONSE:
            self._device_info = self._protocol.parse_device_info(response.payload)
            logger.info(f"Device info: {self._device_info}")
            return True

        return False

    def ping(self) -> float:
        """
        Ping the device and measure latency.

        Returns:
            Round-trip time in milliseconds, or -1 on failure
        """
        start = time.time()
        data = self._protocol.create_ping()
        response = self._send_and_wait(data, MessageType.PONG, timeout=1.0)

        if response and response.message_type == MessageType.PONG:
            rtt = (time.time() - start) * 1000
            self._stats.last_ping_ms = rtt
            return rtt

        return -1.0

    def get_configuration(self) -> Optional[bytes]:
        """
        Read configuration from device.

        Returns:
            Configuration data (JSON bytes) or None on failure
        """
        data = self._protocol.create_get_config()

        if not self._transport or not self._transport.send(data):
            return None

        # Collect config chunks
        timeout = 5.0
        start = time.time()
        config_data = None

        while time.time() - start < timeout:
            if self._response_event.wait(timeout=0.5):
                with self._lock:
                    response = self._pending_response
                    self._pending_response = None
                    self._response_event.clear()

                if response and response.message_type == MessageType.CONFIG_CHUNK:
                    result = self._protocol.process_config_chunk(response.payload)
                    if result:
                        config_data = result
                        break

        return config_data

    def set_configuration(self, config_data: bytes) -> bool:
        """
        Write configuration to device.

        Args:
            config_data: Configuration data (JSON bytes)

        Returns:
            True if successful
        """
        frames = self._protocol.create_set_config(config_data)

        for frame_data in frames:
            response = self._send_and_wait(frame_data, MessageType.CONFIG_CHUNK_ACK)
            if not response or response.message_type != MessageType.CONFIG_CHUNK_ACK:
                logger.error("Config chunk not acknowledged")
                return False

        logger.info("Configuration sent successfully")
        return True

    def subscribe_telemetry(self, rate_hz: int = 50) -> bool:
        """
        Subscribe to telemetry streaming.

        Args:
            rate_hz: Telemetry rate in Hz

        Returns:
            True if successful
        """
        data = self._protocol.create_subscribe_telemetry(rate_hz)
        response = self._send_and_wait(data, MessageType.ACK)
        return response is not None

    def unsubscribe_telemetry(self) -> bool:
        """
        Unsubscribe from telemetry streaming.

        Returns:
            True if successful
        """
        data = self._protocol.create_unsubscribe_telemetry()
        response = self._send_and_wait(data, MessageType.ACK)
        return response is not None

    def set_channel(self, channel_id: int, value: int) -> bool:
        """
        Set a channel value on the device.

        Args:
            channel_id: Channel ID
            value: New value

        Returns:
            True if successful
        """
        data = self._protocol.create_set_channel(channel_id, value)
        response = self._send_and_wait(data, MessageType.CHANNEL_ACK)
        return response is not None

    def save_to_flash(self) -> bool:
        """
        Save current configuration to flash memory.

        Returns:
            True if successful
        """
        data = self._protocol.create_save_to_flash()
        response = self._send_and_wait(data, MessageType.ACK, timeout=5.0)
        return response is not None

    def restart_device(self) -> bool:
        """
        Restart the device.

        Returns:
            True if command sent successfully
        """
        data = self._protocol.create_restart()
        if self._transport:
            return self._transport.send(data)
        return False
