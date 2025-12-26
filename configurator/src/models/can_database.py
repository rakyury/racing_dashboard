# CAN Database Model
"""CAN message and signal definitions, DBC file support."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum


class ByteOrder(Enum):
    """Signal byte order."""
    LITTLE_ENDIAN = 0  # Intel
    BIG_ENDIAN = 1     # Motorola


class ValueType(Enum):
    """Signal value type."""
    UNSIGNED = "+"
    SIGNED = "-"


@dataclass
class CANSignal:
    """CAN signal definition."""
    name: str
    start_bit: int
    bit_length: int
    byte_order: ByteOrder = ByteOrder.BIG_ENDIAN
    value_type: ValueType = ValueType.UNSIGNED
    scale: float = 1.0
    offset: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    unit: str = ""
    comment: str = ""

    # Mapping to channel
    channel_id: Optional[int] = None

    def decode(self, data: bytes) -> float:
        """Decode signal value from CAN data."""
        if len(data) < 8:
            data = data + bytes(8 - len(data))

        # Extract raw value based on byte order
        if self.byte_order == ByteOrder.BIG_ENDIAN:
            raw = self._extract_big_endian(data)
        else:
            raw = self._extract_little_endian(data)

        # Apply sign
        if self.value_type == ValueType.SIGNED:
            if raw >= (1 << (self.bit_length - 1)):
                raw -= (1 << self.bit_length)

        # Apply scale and offset
        return raw * self.scale + self.offset

    def encode(self, value: float) -> Tuple[int, int, int]:
        """Encode value to raw bits. Returns (raw_value, start_bit, bit_length)."""
        # Remove offset and scale
        raw = int((value - self.offset) / self.scale)

        # Clamp to valid range
        max_val = (1 << self.bit_length) - 1
        if self.value_type == ValueType.SIGNED:
            min_val = -(1 << (self.bit_length - 1))
            max_val = (1 << (self.bit_length - 1)) - 1
        else:
            min_val = 0

        raw = max(min_val, min(max_val, raw))

        # Convert negative to two's complement
        if raw < 0:
            raw += (1 << self.bit_length)

        return raw, self.start_bit, self.bit_length

    def _extract_big_endian(self, data: bytes) -> int:
        """Extract value from big endian (Motorola) format."""
        start_byte = self.start_bit // 8
        start_bit_in_byte = self.start_bit % 8

        result = 0
        bits_remaining = self.bit_length
        current_bit = start_bit_in_byte
        current_byte = start_byte

        while bits_remaining > 0:
            bits_in_this_byte = min(current_bit + 1, bits_remaining)
            mask = (1 << bits_in_this_byte) - 1
            shift = current_bit - bits_in_this_byte + 1

            result = (result << bits_in_this_byte) | ((data[current_byte] >> shift) & mask)

            bits_remaining -= bits_in_this_byte
            current_byte += 1
            current_bit = 7

        return result

    def _extract_little_endian(self, data: bytes) -> int:
        """Extract value from little endian (Intel) format."""
        start_byte = self.start_bit // 8
        start_bit_in_byte = self.start_bit % 8

        result = 0
        bits_remaining = self.bit_length
        current_bit = start_bit_in_byte
        current_byte = start_byte
        bit_position = 0

        while bits_remaining > 0:
            bits_in_this_byte = min(8 - current_bit, bits_remaining)
            mask = (1 << bits_in_this_byte) - 1

            result |= ((data[current_byte] >> current_bit) & mask) << bit_position

            bit_position += bits_in_this_byte
            bits_remaining -= bits_in_this_byte
            current_byte += 1
            current_bit = 0

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "start_bit": self.start_bit,
            "bit_length": self.bit_length,
            "byte_order": "big" if self.byte_order == ByteOrder.BIG_ENDIAN else "little",
            "value_type": "signed" if self.value_type == ValueType.SIGNED else "unsigned",
            "scale": self.scale,
            "offset": self.offset,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "comment": self.comment,
            "channel_id": self.channel_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CANSignal":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            start_bit=data.get("start_bit", 0),
            bit_length=data.get("bit_length", 8),
            byte_order=ByteOrder.BIG_ENDIAN if data.get("byte_order", "big") == "big" else ByteOrder.LITTLE_ENDIAN,
            value_type=ValueType.SIGNED if data.get("value_type", "unsigned") == "signed" else ValueType.UNSIGNED,
            scale=data.get("scale", 1.0),
            offset=data.get("offset", 0.0),
            min_value=data.get("min_value", 0.0),
            max_value=data.get("max_value", 0.0),
            unit=data.get("unit", ""),
            comment=data.get("comment", ""),
            channel_id=data.get("channel_id"),
        )


@dataclass
class CANMessage:
    """CAN message definition."""
    id: int
    name: str
    dlc: int = 8
    extended: bool = False
    signals: List[CANSignal] = field(default_factory=list)
    comment: str = ""
    cycle_time_ms: int = 0  # 0 = event-driven
    transmitter: str = ""

    def add_signal(self, signal: CANSignal) -> None:
        """Add signal to message."""
        self.signals.append(signal)

    def remove_signal(self, signal_name: str) -> bool:
        """Remove signal by name."""
        for i, sig in enumerate(self.signals):
            if sig.name == signal_name:
                self.signals.pop(i)
                return True
        return False

    def get_signal(self, name: str) -> Optional[CANSignal]:
        """Get signal by name."""
        for sig in self.signals:
            if sig.name == name:
                return sig
        return None

    def decode_all(self, data: bytes) -> Dict[str, float]:
        """Decode all signals from CAN data."""
        result = {}
        for signal in self.signals:
            try:
                result[signal.name] = signal.decode(data)
            except Exception:
                result[signal.name] = 0.0
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "dlc": self.dlc,
            "extended": self.extended,
            "signals": [s.to_dict() for s in self.signals],
            "comment": self.comment,
            "cycle_time_ms": self.cycle_time_ms,
            "transmitter": self.transmitter,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CANMessage":
        """Create from dictionary."""
        msg = cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            dlc=data.get("dlc", 8),
            extended=data.get("extended", False),
            comment=data.get("comment", ""),
            cycle_time_ms=data.get("cycle_time_ms", 0),
            transmitter=data.get("transmitter", ""),
        )
        for sig_data in data.get("signals", []):
            msg.signals.append(CANSignal.from_dict(sig_data))
        return msg


@dataclass
class CANDatabase:
    """CAN database containing messages and signals."""
    name: str = "Untitled"
    version: str = "1.0"
    messages: List[CANMessage] = field(default_factory=list)
    comment: str = ""

    def add_message(self, message: CANMessage) -> None:
        """Add message to database."""
        self.messages.append(message)

    def remove_message(self, message_id: int) -> bool:
        """Remove message by ID."""
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                self.messages.pop(i)
                return True
        return False

    def get_message(self, message_id: int) -> Optional[CANMessage]:
        """Get message by ID."""
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        return None

    def get_message_by_name(self, name: str) -> Optional[CANMessage]:
        """Get message by name."""
        for msg in self.messages:
            if msg.name == name:
                return msg
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "messages": [m.to_dict() for m in self.messages],
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CANDatabase":
        """Create from dictionary."""
        db = cls(
            name=data.get("name", "Untitled"),
            version=data.get("version", "1.0"),
            comment=data.get("comment", ""),
        )
        for msg_data in data.get("messages", []):
            db.messages.append(CANMessage.from_dict(msg_data))
        return db


# =============================================================================
# DBC File Parser
# =============================================================================

class DBCParser:
    """Parser for Vector DBC files."""

    @staticmethod
    def parse(content: str) -> CANDatabase:
        """Parse DBC file content."""
        db = CANDatabase()
        lines = content.split('\n')

        current_message: Optional[CANMessage] = None

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                continue

            # Version
            if line.startswith('VERSION'):
                match = re.match(r'VERSION\s+"([^"]*)"', line)
                if match:
                    db.version = match.group(1)

            # Message definition
            elif line.startswith('BO_'):
                match = re.match(r'BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+)', line)
                if match:
                    msg_id = int(match.group(1))
                    msg_name = match.group(2)
                    dlc = int(match.group(3))
                    transmitter = match.group(4)

                    current_message = CANMessage(
                        id=msg_id,
                        name=msg_name,
                        dlc=dlc,
                        transmitter=transmitter
                    )
                    db.add_message(current_message)

            # Signal definition
            elif line.startswith('SG_') and current_message:
                match = re.match(
                    r'SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*'
                    r'\(([^,]+),([^)]+)\)\s*\[([^\|]*)\|([^\]]*)\]\s*"([^"]*)"\s*(.*)',
                    line
                )
                if match:
                    signal = CANSignal(
                        name=match.group(1),
                        start_bit=int(match.group(2)),
                        bit_length=int(match.group(3)),
                        byte_order=ByteOrder.LITTLE_ENDIAN if match.group(4) == '1' else ByteOrder.BIG_ENDIAN,
                        value_type=ValueType.SIGNED if match.group(5) == '-' else ValueType.UNSIGNED,
                        scale=float(match.group(6)),
                        offset=float(match.group(7)),
                        min_value=float(match.group(8)) if match.group(8) else 0.0,
                        max_value=float(match.group(9)) if match.group(9) else 0.0,
                        unit=match.group(10),
                    )
                    current_message.add_signal(signal)

            # Comment for message
            elif line.startswith('CM_'):
                # Message comment
                match = re.match(r'CM_\s+BO_\s+(\d+)\s+"([^"]*)";', line)
                if match:
                    msg_id = int(match.group(1))
                    msg = db.get_message(msg_id)
                    if msg:
                        msg.comment = match.group(2)

                # Signal comment
                match = re.match(r'CM_\s+SG_\s+(\d+)\s+(\w+)\s+"([^"]*)";', line)
                if match:
                    msg_id = int(match.group(1))
                    sig_name = match.group(2)
                    msg = db.get_message(msg_id)
                    if msg:
                        sig = msg.get_signal(sig_name)
                        if sig:
                            sig.comment = match.group(3)

        return db

    @staticmethod
    def parse_file(file_path: str) -> CANDatabase:
        """Parse DBC file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return DBCParser.parse(content)

    @staticmethod
    def export(db: CANDatabase) -> str:
        """Export database to DBC format."""
        lines = []

        # Header
        lines.append(f'VERSION "{db.version}"')
        lines.append('')
        lines.append('NS_ :')
        lines.append('')
        lines.append('BS_:')
        lines.append('')
        lines.append('BU_:')
        lines.append('')

        # Messages and signals
        for msg in db.messages:
            lines.append(f'BO_ {msg.id} {msg.name}: {msg.dlc} {msg.transmitter or "Vector__XXX"}')

            for sig in msg.signals:
                byte_order = '1' if sig.byte_order == ByteOrder.LITTLE_ENDIAN else '0'
                value_type = '-' if sig.value_type == ValueType.SIGNED else '+'
                lines.append(
                    f' SG_ {sig.name} : {sig.start_bit}|{sig.bit_length}@{byte_order}{value_type} '
                    f'({sig.scale},{sig.offset}) [{sig.min_value}|{sig.max_value}] "{sig.unit}" Vector__XXX'
                )

            lines.append('')

        # Comments
        for msg in db.messages:
            if msg.comment:
                lines.append(f'CM_ BO_ {msg.id} "{msg.comment}";')
            for sig in msg.signals:
                if sig.comment:
                    lines.append(f'CM_ SG_ {msg.id} {sig.name} "{sig.comment}";')

        return '\n'.join(lines)

    @staticmethod
    def export_file(db: CANDatabase, file_path: str) -> None:
        """Export database to DBC file."""
        content = DBCParser.export(db)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
