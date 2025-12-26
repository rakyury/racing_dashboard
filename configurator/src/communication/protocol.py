# Binary Protocol
"""Binary communication protocol for Racing Dashboard device."""

import struct
import logging
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Tuple, List
import zlib

logger = logging.getLogger(__name__)


class MessageType(IntEnum):
    """Protocol message types."""
    # System
    PING = 0x01
    PONG = 0x02
    ACK = 0x03
    NACK = 0x04
    ERROR = 0x05

    # Device info
    GET_INFO = 0x10
    INFO_RESPONSE = 0x11

    # Configuration
    GET_CONFIG = 0x20
    CONFIG_DATA = 0x21
    SET_CONFIG = 0x22
    CONFIG_ACK = 0x23
    CONFIG_CHUNK = 0x24
    CONFIG_CHUNK_ACK = 0x25
    CONFIG_COMPLETE = 0x26

    # Telemetry
    SUBSCRIBE_TELEMETRY = 0x30
    UNSUBSCRIBE_TELEMETRY = 0x31
    TELEMETRY_DATA = 0x32

    # Control
    SET_CHANNEL = 0x40
    CHANNEL_ACK = 0x41
    RESTART_DEVICE = 0x42
    SAVE_TO_FLASH = 0x43

    # Logging
    LOG_MESSAGE = 0x50
    START_LOGGING = 0x51
    STOP_LOGGING = 0x52

    # OTA
    OTA_START = 0x60
    OTA_DATA = 0x61
    OTA_VERIFY = 0x62
    OTA_COMMIT = 0x63
    OTA_STATUS = 0x64


class ErrorCode(IntEnum):
    """Protocol error codes."""
    OK = 0x00
    UNKNOWN_MESSAGE = 0x01
    INVALID_PAYLOAD = 0x02
    CRC_ERROR = 0x03
    TIMEOUT = 0x04
    BUSY = 0x05
    NOT_SUPPORTED = 0x06
    FLASH_ERROR = 0x07
    CONFIG_INVALID = 0x08


# Protocol constants
HEADER_BYTE = 0xAA
FOOTER_BYTE = 0x55
MAX_PAYLOAD_SIZE = 4096
CHUNK_SIZE = 1024


@dataclass
class ProtocolFrame:
    """A single protocol frame."""
    message_type: MessageType
    payload: bytes = b""
    sequence: int = 0

    @property
    def length(self) -> int:
        return len(self.payload)


def calculate_crc16(data: bytes) -> int:
    """Calculate CRC-16-CCITT checksum."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def encode_frame(frame: ProtocolFrame) -> bytes:
    """
    Encode a protocol frame to bytes.

    Frame format:
    +--------+--------+--------+--------+---------+--------+--------+
    | Header | SeqNum | MsgType| LenLo  | LenHi   |Payload | CRC16  | Footer |
    | 0xAA   | 1 byte | 1 byte | 1 byte | 1 byte  | N bytes| 2 bytes| 0x55   |
    +--------+--------+--------+--------+---------+--------+--------+--------+
    """
    # Build frame without CRC
    header = struct.pack(
        '<BBBH',
        HEADER_BYTE,
        frame.sequence & 0xFF,
        frame.message_type,
        len(frame.payload)
    )

    # Calculate CRC over header (excluding start byte) and payload
    crc_data = header[1:] + frame.payload
    crc = calculate_crc16(crc_data)

    # Build complete frame
    return header + frame.payload + struct.pack('<HB', crc, FOOTER_BYTE)


def decode_frame(data: bytes) -> Tuple[Optional[ProtocolFrame], int]:
    """
    Decode a protocol frame from bytes.

    Args:
        data: Input byte buffer

    Returns:
        Tuple of (decoded frame or None, bytes consumed)
    """
    # Minimum frame size: header(5) + crc(2) + footer(1) = 8 bytes
    if len(data) < 8:
        return (None, 0)

    # Find header
    try:
        start_idx = data.index(HEADER_BYTE)
    except ValueError:
        return (None, len(data))  # Discard all, no header found

    # Check if we have enough data for header
    if len(data) - start_idx < 8:
        return (None, start_idx)  # Keep from header onwards

    # Parse header
    try:
        header = data[start_idx:start_idx + 5]
        _, seq, msg_type, payload_len = struct.unpack('<BBBH', header)
    except struct.error:
        return (None, start_idx + 1)  # Skip this header byte

    # Check if we have complete frame
    frame_len = 5 + payload_len + 3  # header + payload + crc + footer
    if len(data) - start_idx < frame_len:
        return (None, start_idx)  # Wait for more data

    # Extract payload and CRC
    payload = data[start_idx + 5:start_idx + 5 + payload_len]
    crc_footer = data[start_idx + 5 + payload_len:start_idx + frame_len]

    try:
        received_crc, footer = struct.unpack('<HB', crc_footer)
    except struct.error:
        return (None, start_idx + 1)

    # Verify footer
    if footer != FOOTER_BYTE:
        logger.warning("Invalid footer byte")
        return (None, start_idx + 1)

    # Verify CRC
    crc_data = header[1:] + payload
    calculated_crc = calculate_crc16(crc_data)
    if received_crc != calculated_crc:
        logger.warning(f"CRC mismatch: received {received_crc:04X}, calculated {calculated_crc:04X}")
        return (None, start_idx + 1)

    # Valid frame
    try:
        message_type = MessageType(msg_type)
    except ValueError:
        logger.warning(f"Unknown message type: {msg_type}")
        return (None, start_idx + frame_len)

    frame = ProtocolFrame(
        message_type=message_type,
        payload=payload,
        sequence=seq
    )

    return (frame, start_idx + frame_len)


class Protocol:
    """
    High-level protocol handler.
    Manages framing, sequencing, and message encoding/decoding.
    """

    def __init__(self):
        self._sequence = 0
        self._rx_buffer = bytearray()
        self._pending_chunks: List[bytes] = []
        self._chunk_total = 0
        self._chunk_received = 0

    def next_sequence(self) -> int:
        """Get next sequence number."""
        seq = self._sequence
        self._sequence = (self._sequence + 1) & 0xFF
        return seq

    def create_ping(self) -> bytes:
        """Create a ping message."""
        frame = ProtocolFrame(MessageType.PING, b"", self.next_sequence())
        return encode_frame(frame)

    def create_get_info(self) -> bytes:
        """Create a get device info message."""
        frame = ProtocolFrame(MessageType.GET_INFO, b"", self.next_sequence())
        return encode_frame(frame)

    def create_get_config(self) -> bytes:
        """Create a get configuration message."""
        frame = ProtocolFrame(MessageType.GET_CONFIG, b"", self.next_sequence())
        return encode_frame(frame)

    def create_set_config(self, config_data: bytes) -> List[bytes]:
        """
        Create set configuration messages (chunked if necessary).

        Args:
            config_data: Configuration data (JSON bytes)

        Returns:
            List of encoded frame bytes
        """
        frames = []

        # Compress data if large
        if len(config_data) > 1024:
            compressed = zlib.compress(config_data, level=6)
            if len(compressed) < len(config_data):
                config_data = compressed
                is_compressed = True
            else:
                is_compressed = False
        else:
            is_compressed = False

        total_chunks = (len(config_data) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for i in range(total_chunks):
            chunk_start = i * CHUNK_SIZE
            chunk_end = min((i + 1) * CHUNK_SIZE, len(config_data))
            chunk_data = config_data[chunk_start:chunk_end]

            # Chunk header: chunk_idx (2), total_chunks (2), compressed (1)
            chunk_header = struct.pack('<HHB', i, total_chunks, 1 if is_compressed else 0)
            payload = chunk_header + chunk_data

            frame = ProtocolFrame(MessageType.CONFIG_CHUNK, payload, self.next_sequence())
            frames.append(encode_frame(frame))

        return frames

    def create_subscribe_telemetry(self, rate_hz: int = 50) -> bytes:
        """Create a subscribe telemetry message."""
        payload = struct.pack('<H', rate_hz)
        frame = ProtocolFrame(MessageType.SUBSCRIBE_TELEMETRY, payload, self.next_sequence())
        return encode_frame(frame)

    def create_unsubscribe_telemetry(self) -> bytes:
        """Create an unsubscribe telemetry message."""
        frame = ProtocolFrame(MessageType.UNSUBSCRIBE_TELEMETRY, b"", self.next_sequence())
        return encode_frame(frame)

    def create_set_channel(self, channel_id: int, value: int) -> bytes:
        """Create a set channel value message."""
        payload = struct.pack('<HI', channel_id, value)
        frame = ProtocolFrame(MessageType.SET_CHANNEL, payload, self.next_sequence())
        return encode_frame(frame)

    def create_restart(self) -> bytes:
        """Create a restart device message."""
        frame = ProtocolFrame(MessageType.RESTART_DEVICE, b"", self.next_sequence())
        return encode_frame(frame)

    def create_save_to_flash(self) -> bytes:
        """Create a save to flash message."""
        frame = ProtocolFrame(MessageType.SAVE_TO_FLASH, b"", self.next_sequence())
        return encode_frame(frame)

    def feed_data(self, data: bytes) -> List[ProtocolFrame]:
        """
        Feed received data and extract complete frames.

        Args:
            data: Received bytes

        Returns:
            List of decoded frames
        """
        self._rx_buffer.extend(data)
        frames = []

        while True:
            frame, consumed = decode_frame(bytes(self._rx_buffer))
            if frame is None:
                if consumed > 0:
                    self._rx_buffer = self._rx_buffer[consumed:]
                break
            else:
                frames.append(frame)
                self._rx_buffer = self._rx_buffer[consumed:]

        return frames

    def process_config_chunk(self, payload: bytes) -> Optional[bytes]:
        """
        Process a config chunk and return complete config when all received.

        Args:
            payload: Chunk payload

        Returns:
            Complete config data when all chunks received, None otherwise
        """
        chunk_idx, total_chunks, is_compressed = struct.unpack('<HHB', payload[:5])
        chunk_data = payload[5:]

        if chunk_idx == 0:
            self._pending_chunks = [None] * total_chunks
            self._chunk_total = total_chunks
            self._chunk_received = 0

        if chunk_idx < len(self._pending_chunks):
            self._pending_chunks[chunk_idx] = chunk_data
            self._chunk_received += 1

        if self._chunk_received == self._chunk_total:
            # Reassemble
            complete_data = b''.join(self._pending_chunks)
            self._pending_chunks = []

            if is_compressed:
                complete_data = zlib.decompress(complete_data)

            return complete_data

        return None

    def parse_device_info(self, payload: bytes) -> dict:
        """Parse device info response payload."""
        # Format: firmware_version (16), serial (16), hw_version (8)
        if len(payload) < 40:
            return {}

        fw_version = payload[:16].rstrip(b'\x00').decode('utf-8', errors='ignore')
        serial = payload[16:32].rstrip(b'\x00').decode('utf-8', errors='ignore')
        hw_version = payload[32:40].rstrip(b'\x00').decode('utf-8', errors='ignore')

        return {
            "firmware_version": fw_version,
            "serial_number": serial,
            "hardware_version": hw_version,
        }

    def parse_telemetry(self, payload: bytes) -> dict:
        """Parse telemetry data payload."""
        if len(payload) < 32:
            return {}

        # Basic telemetry format
        try:
            (
                timestamp_ms,
                rpm,
                speed_kmh,
                gear,
                throttle,
                brake,
                coolant_temp,
                oil_temp,
                fuel_level,
                g_lat,
                g_lon,
                lap_time_ms,
            ) = struct.unpack('<IHHBBBbbBhhI', payload[:24])

            return {
                "timestamp_ms": timestamp_ms,
                "rpm": rpm,
                "speed_kmh": speed_kmh,
                "gear": gear,
                "throttle_percent": throttle,
                "brake_percent": brake,
                "coolant_temp_c": coolant_temp,
                "oil_temp_c": oil_temp,
                "fuel_level_percent": fuel_level,
                "g_lateral": g_lat / 100.0,
                "g_longitudinal": g_lon / 100.0,
                "lap_time_ms": lap_time_ms,
            }
        except struct.error as e:
            logger.error(f"Failed to parse telemetry: {e}")
            return {}

    def parse_error(self, payload: bytes) -> Tuple[ErrorCode, str]:
        """Parse error response payload."""
        if len(payload) < 1:
            return (ErrorCode.UNKNOWN_MESSAGE, "Unknown error")

        error_code = ErrorCode(payload[0])
        message = payload[1:].decode('utf-8', errors='ignore') if len(payload) > 1 else ""
        return (error_code, message)
