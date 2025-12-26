# Transport Base
"""Abstract base class for communication transports."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, List, AsyncIterator
import logging

logger = logging.getLogger(__name__)


class TransportState(Enum):
    """Transport connection state."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()


@dataclass
class TransportInfo:
    """Information about an available transport/port."""
    port: str
    description: str
    hardware_id: str = ""
    manufacturer: str = ""
    is_racing_dashboard: bool = False


class TransportBase(ABC):
    """
    Abstract base class for communication transports.
    Implementations include Serial, WiFi, Emulator, etc.
    """

    def __init__(self):
        self._state = TransportState.DISCONNECTED
        self._state_callback: Optional[Callable[[TransportState], None]] = None
        self._data_callback: Optional[Callable[[bytes], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None

    @property
    def state(self) -> TransportState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._state == TransportState.CONNECTED

    def set_state_callback(self, callback: Callable[[TransportState], None]) -> None:
        """Set callback for state changes."""
        self._state_callback = callback

    def set_data_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for received data."""
        self._data_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for errors."""
        self._error_callback = callback

    def _set_state(self, state: TransportState) -> None:
        """Update state and notify callback."""
        if state != self._state:
            old_state = self._state
            self._state = state
            logger.debug(f"Transport state: {old_state.name} -> {state.name}")
            if self._state_callback:
                try:
                    self._state_callback(state)
                except Exception as e:
                    logger.error(f"State callback error: {e}")

    def _on_data_received(self, data: bytes) -> None:
        """Called when data is received."""
        if self._data_callback:
            try:
                self._data_callback(data)
            except Exception as e:
                logger.error(f"Data callback error: {e}")

    def _on_error(self, message: str) -> None:
        """Called when an error occurs."""
        logger.error(f"Transport error: {message}")
        if self._error_callback:
            try:
                self._error_callback(message)
            except Exception as e:
                logger.error(f"Error callback error: {e}")

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        Connect to the device.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the device."""
        pass

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """
        Send data to the device.

        Args:
            data: Data to send

        Returns:
            True if send successful
        """
        pass

    @abstractmethod
    def receive(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Receive data from the device (blocking).

        Args:
            timeout: Receive timeout in seconds

        Returns:
            Received data or None on timeout
        """
        pass

    @staticmethod
    @abstractmethod
    def list_ports() -> List[TransportInfo]:
        """
        List available ports/connections.

        Returns:
            List of available transport info
        """
        pass


class TransportError(Exception):
    """Exception for transport errors."""
    pass
