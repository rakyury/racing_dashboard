# Serial Transport
"""USB Serial transport implementation."""

import logging
import threading
import time
from typing import Optional, List

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from .transport_base import TransportBase, TransportState, TransportInfo, TransportError

logger = logging.getLogger(__name__)

# Racing Dashboard USB identifiers
RACING_DASHBOARD_VID = 0x0483  # STMicroelectronics
RACING_DASHBOARD_PID = 0x5740  # Virtual COM Port


class SerialTransport(TransportBase):
    """
    USB Serial transport for Racing Dashboard devices.
    Uses pyserial for communication.
    """

    def __init__(self):
        super().__init__()
        self._serial: Optional[serial.Serial] = None
        self._port: Optional[str] = None
        self._read_thread: Optional[threading.Thread] = None
        self._running = False
        self._rx_buffer = bytearray()
        self._rx_lock = threading.Lock()

    def connect(self, port: str = None, baudrate: int = 115200, **kwargs) -> bool:
        """
        Connect to a serial port.

        Args:
            port: Serial port name (e.g., "COM3", "/dev/ttyUSB0")
            baudrate: Baud rate (default 115200)

        Returns:
            True if connection successful
        """
        if not SERIAL_AVAILABLE:
            self._on_error("pyserial not installed")
            return False

        if self._state == TransportState.CONNECTED:
            logger.warning("Already connected")
            return True

        self._set_state(TransportState.CONNECTING)

        # Auto-detect port if not specified
        if port is None:
            ports = self.list_ports()
            racing_ports = [p for p in ports if p.is_racing_dashboard]
            if racing_ports:
                port = racing_ports[0].port
                logger.info(f"Auto-detected Racing Dashboard on {port}")
            elif ports:
                port = ports[0].port
                logger.info(f"Using first available port: {port}")
            else:
                self._on_error("No serial ports found")
                self._set_state(TransportState.DISCONNECTED)
                return False

        try:
            logger.info(f"Connecting to {port} at {baudrate} baud")

            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=0.1,
                write_timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

            self._port = port
            self._running = True

            # Start read thread
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()

            self._set_state(TransportState.CONNECTED)
            logger.info(f"Connected to {port}")
            return True

        except serial.SerialException as e:
            self._on_error(f"Failed to connect: {e}")
            self._set_state(TransportState.ERROR)
            return False

    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        if self._state == TransportState.DISCONNECTED:
            return

        logger.info("Disconnecting from serial port")

        self._running = False

        # Wait for read thread to stop
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)

        # Close serial port
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception as e:
                logger.error(f"Error closing serial port: {e}")

        self._serial = None
        self._port = None
        self._set_state(TransportState.DISCONNECTED)
        logger.info("Disconnected")

    def send(self, data: bytes) -> bool:
        """
        Send data over the serial port.

        Args:
            data: Data to send

        Returns:
            True if send successful
        """
        if not self.is_connected or self._serial is None:
            logger.error("Not connected")
            return False

        try:
            bytes_written = self._serial.write(data)
            self._serial.flush()
            logger.debug(f"Sent {bytes_written} bytes")
            return bytes_written == len(data)

        except serial.SerialException as e:
            self._on_error(f"Send error: {e}")
            self._set_state(TransportState.ERROR)
            return False

    def receive(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Receive data from the serial port.

        Args:
            timeout: Receive timeout in seconds

        Returns:
            Received data or None on timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._rx_lock:
                if self._rx_buffer:
                    data = bytes(self._rx_buffer)
                    self._rx_buffer.clear()
                    return data
            time.sleep(0.01)

        return None

    def _read_loop(self) -> None:
        """Background thread for reading serial data."""
        while self._running and self._serial and self._serial.is_open:
            try:
                # Read available data
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    if data:
                        with self._rx_lock:
                            self._rx_buffer.extend(data)
                        self._on_data_received(data)
                else:
                    time.sleep(0.01)

            except serial.SerialException as e:
                if self._running:
                    self._on_error(f"Read error: {e}")
                    self._set_state(TransportState.ERROR)
                break

            except Exception as e:
                if self._running:
                    logger.error(f"Unexpected error in read loop: {e}")
                break

    @staticmethod
    def list_ports() -> List[TransportInfo]:
        """
        List available serial ports.

        Returns:
            List of available port info
        """
        if not SERIAL_AVAILABLE:
            return []

        ports = []
        for port in serial.tools.list_ports.comports():
            is_racing_dashboard = (
                port.vid == RACING_DASHBOARD_VID and
                port.pid == RACING_DASHBOARD_PID
            )

            info = TransportInfo(
                port=port.device,
                description=port.description or "",
                hardware_id=port.hwid or "",
                manufacturer=port.manufacturer or "",
                is_racing_dashboard=is_racing_dashboard,
            )
            ports.append(info)

        return ports

    @staticmethod
    def find_racing_dashboard() -> Optional[str]:
        """
        Find a connected Racing Dashboard device.

        Returns:
            Port name or None if not found
        """
        ports = SerialTransport.list_ports()
        for port in ports:
            if port.is_racing_dashboard:
                return port.port
        return None
