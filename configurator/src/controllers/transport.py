# Transport Factory
"""Factory for creating transport instances."""

from typing import Optional, Dict, Any
from enum import Enum, auto

from communication.transport_base import TransportBase
from communication.serial_transport import SerialTransport
from communication.emulator_transport import EmulatorTransport


class TransportType(Enum):
    """Available transport types."""
    SERIAL = auto()
    WIFI = auto()
    EMULATOR = auto()


class TransportFactory:
    """Factory for creating transport instances."""

    @staticmethod
    def create(transport_type: TransportType, **kwargs) -> TransportBase:
        """
        Create a transport instance.

        Args:
            transport_type: Type of transport to create
            **kwargs: Transport-specific parameters

        Returns:
            Transport instance

        Raises:
            ValueError: If transport type is not supported
        """
        if transport_type == TransportType.SERIAL:
            return SerialTransport()

        elif transport_type == TransportType.EMULATOR:
            return EmulatorTransport()

        elif transport_type == TransportType.WIFI:
            # WiFi transport not implemented yet
            raise ValueError("WiFi transport not yet implemented")

        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> TransportBase:
        """
        Create a transport from configuration dictionary.

        Args:
            config: Configuration dictionary with 'type' and optional parameters

        Returns:
            Transport instance
        """
        transport_type_str = config.get("type", "serial").lower()

        if transport_type_str == "serial":
            return TransportFactory.create(TransportType.SERIAL)

        elif transport_type_str == "emulator":
            return TransportFactory.create(TransportType.EMULATOR)

        elif transport_type_str == "wifi":
            return TransportFactory.create(TransportType.WIFI)

        else:
            raise ValueError(f"Unknown transport type: {transport_type_str}")

    @staticmethod
    def get_available_types() -> list:
        """Get list of available transport types."""
        return [
            TransportType.SERIAL,
            TransportType.EMULATOR,
            # TransportType.WIFI,  # Not yet implemented
        ]
