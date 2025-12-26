# Channel Types for Racing Dashboard
"""Data channel definitions and predefined channels."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class ChannelType(Enum):
    """Channel source type."""
    SYSTEM = "system"
    CAN_RX = "can_rx"
    CAN_TX = "can_tx"
    ANALOG = "analog"
    DIGITAL = "digital"
    GPS = "gps"
    LAPTIMER = "laptimer"
    LOGIC = "logic"
    CONSTANT = "constant"


class AnalogInputType(Enum):
    """Analog input types."""
    VOLTAGE = "voltage"
    VOLTAGE_DIVIDER = "voltage_divider"
    CURRENT_4_20MA = "current_4_20ma"
    THERMISTOR_NTC = "thermistor_ntc"
    THERMISTOR_PTC = "thermistor_ptc"
    RESISTANCE = "resistance"


class DigitalInputType(Enum):
    """Digital input types."""
    ON_OFF = "on_off"
    FREQUENCY = "frequency"
    PULSE_COUNT = "pulse_count"
    PWM_DUTY = "pwm_duty"
    SPEED = "speed"


class CANByteOrder(Enum):
    """CAN byte order."""
    LITTLE_ENDIAN = "little"
    BIG_ENDIAN = "big"


class CANDataType(Enum):
    """CAN data types."""
    UNSIGNED = "unsigned"
    SIGNED = "signed"
    FLOAT32 = "float32"


@dataclass
class ChannelDefinition:
    """Channel definition."""
    id: int
    name: str
    units: str = ""
    channel_type: ChannelType = ChannelType.CAN_RX
    decimals: int = 0
    min_value: float = 0.0
    max_value: float = 100.0
    warning_low: Optional[float] = None
    warning_high: Optional[float] = None
    danger_low: Optional[float] = None
    danger_high: Optional[float] = None
    category: str = "General"
    description: str = ""

    # CAN specific
    can_message_id: int = 0
    can_start_bit: int = 0
    can_bit_length: int = 16
    can_byte_order: CANByteOrder = CANByteOrder.BIG_ENDIAN
    can_data_type: CANDataType = CANDataType.UNSIGNED
    can_scale: float = 1.0
    can_offset: float = 0.0
    can_timeout_ms: int = 500

    # Analog specific
    analog_input_type: AnalogInputType = AnalogInputType.VOLTAGE
    analog_channel: int = 0
    analog_scale: float = 1.0
    analog_offset: float = 0.0
    analog_filter_alpha: float = 0.1
    thermistor_beta: float = 3950.0
    thermistor_r25: float = 10000.0
    thermistor_pullup: float = 2200.0

    # Digital specific
    digital_input_type: DigitalInputType = DigitalInputType.ON_OFF
    digital_channel: int = 0
    digital_inverted: bool = False
    digital_debounce_ms: int = 10
    pulses_per_unit: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "name": self.name,
            "units": self.units,
            "type": self.channel_type.value,
            "decimals": self.decimals,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "category": self.category,
        }

        if self.warning_low is not None:
            data["warning_low"] = self.warning_low
        if self.warning_high is not None:
            data["warning_high"] = self.warning_high
        if self.danger_low is not None:
            data["danger_low"] = self.danger_low
        if self.danger_high is not None:
            data["danger_high"] = self.danger_high

        # Add type-specific config
        if self.channel_type == ChannelType.CAN_RX:
            data["can"] = {
                "message_id": self.can_message_id,
                "start_bit": self.can_start_bit,
                "bit_length": self.can_bit_length,
                "byte_order": self.can_byte_order.value,
                "data_type": self.can_data_type.value,
                "scale": self.can_scale,
                "offset": self.can_offset,
                "timeout_ms": self.can_timeout_ms,
            }
        elif self.channel_type == ChannelType.ANALOG:
            data["analog"] = {
                "input_type": self.analog_input_type.value,
                "channel": self.analog_channel,
                "scale": self.analog_scale,
                "offset": self.analog_offset,
                "filter_alpha": self.analog_filter_alpha,
            }
            if self.analog_input_type == AnalogInputType.THERMISTOR_NTC:
                data["analog"]["thermistor_beta"] = self.thermistor_beta
                data["analog"]["thermistor_r25"] = self.thermistor_r25
                data["analog"]["thermistor_pullup"] = self.thermistor_pullup
        elif self.channel_type == ChannelType.DIGITAL:
            data["digital"] = {
                "input_type": self.digital_input_type.value,
                "channel": self.digital_channel,
                "inverted": self.digital_inverted,
                "debounce_ms": self.digital_debounce_ms,
            }
            if self.digital_input_type in (DigitalInputType.FREQUENCY, DigitalInputType.SPEED):
                data["digital"]["pulses_per_unit"] = self.pulses_per_unit

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChannelDefinition":
        """Create from dictionary."""
        channel = cls(
            id=data.get("id", 0),
            name=data.get("name", "Unknown"),
            units=data.get("units", ""),
            channel_type=ChannelType(data.get("type", "can_rx")),
            decimals=data.get("decimals", 0),
            min_value=data.get("min_value", 0.0),
            max_value=data.get("max_value", 100.0),
            warning_low=data.get("warning_low"),
            warning_high=data.get("warning_high"),
            danger_low=data.get("danger_low"),
            danger_high=data.get("danger_high"),
            category=data.get("category", "General"),
        )

        # CAN config
        if "can" in data:
            can = data["can"]
            channel.can_message_id = can.get("message_id", 0)
            channel.can_start_bit = can.get("start_bit", 0)
            channel.can_bit_length = can.get("bit_length", 16)
            channel.can_byte_order = CANByteOrder(can.get("byte_order", "big"))
            channel.can_data_type = CANDataType(can.get("data_type", "unsigned"))
            channel.can_scale = can.get("scale", 1.0)
            channel.can_offset = can.get("offset", 0.0)
            channel.can_timeout_ms = can.get("timeout_ms", 500)

        # Analog config
        if "analog" in data:
            analog = data["analog"]
            channel.analog_input_type = AnalogInputType(analog.get("input_type", "voltage"))
            channel.analog_channel = analog.get("channel", 0)
            channel.analog_scale = analog.get("scale", 1.0)
            channel.analog_offset = analog.get("offset", 0.0)
            channel.analog_filter_alpha = analog.get("filter_alpha", 0.1)
            channel.thermistor_beta = analog.get("thermistor_beta", 3950.0)
            channel.thermistor_r25 = analog.get("thermistor_r25", 10000.0)
            channel.thermistor_pullup = analog.get("thermistor_pullup", 2200.0)

        # Digital config
        if "digital" in data:
            digital = data["digital"]
            channel.digital_input_type = DigitalInputType(digital.get("input_type", "on_off"))
            channel.digital_channel = digital.get("channel", 0)
            channel.digital_inverted = digital.get("inverted", False)
            channel.digital_debounce_ms = digital.get("debounce_ms", 10)
            channel.pulses_per_unit = digital.get("pulses_per_unit", 1.0)

        return channel


# =============================================================================
# Predefined Channels
# =============================================================================

# System channels (900-999)
SYSTEM_CHANNELS = [
    ChannelDefinition(id=900, name="System Voltage", units="V", channel_type=ChannelType.SYSTEM,
                      decimals=1, min_value=0, max_value=20, warning_low=11.5, danger_low=10.5,
                      category="System"),
    ChannelDefinition(id=901, name="MCU Temperature", units="°C", channel_type=ChannelType.SYSTEM,
                      decimals=0, min_value=-40, max_value=125, warning_high=80, danger_high=100,
                      category="System"),
    ChannelDefinition(id=902, name="Uptime", units="s", channel_type=ChannelType.SYSTEM,
                      decimals=0, min_value=0, max_value=999999, category="System"),
    ChannelDefinition(id=903, name="Free Memory", units="B", channel_type=ChannelType.SYSTEM,
                      decimals=0, min_value=0, max_value=500000, category="System"),
    ChannelDefinition(id=904, name="CPU Load", units="%", channel_type=ChannelType.SYSTEM,
                      decimals=0, min_value=0, max_value=100, warning_high=80, danger_high=95,
                      category="System"),
]

# GPS channels (500-549)
GPS_CHANNELS = [
    ChannelDefinition(id=500, name="GPS Latitude", units="°", channel_type=ChannelType.GPS,
                      decimals=6, min_value=-90, max_value=90, category="GPS"),
    ChannelDefinition(id=501, name="GPS Longitude", units="°", channel_type=ChannelType.GPS,
                      decimals=6, min_value=-180, max_value=180, category="GPS"),
    ChannelDefinition(id=502, name="GPS Altitude", units="m", channel_type=ChannelType.GPS,
                      decimals=1, min_value=-100, max_value=10000, category="GPS"),
    ChannelDefinition(id=503, name="GPS Speed", units="km/h", channel_type=ChannelType.GPS,
                      decimals=1, min_value=0, max_value=400, category="GPS"),
    ChannelDefinition(id=504, name="GPS Heading", units="°", channel_type=ChannelType.GPS,
                      decimals=1, min_value=0, max_value=360, category="GPS"),
    ChannelDefinition(id=505, name="GPS Satellites", units="", channel_type=ChannelType.GPS,
                      decimals=0, min_value=0, max_value=32, warning_low=6, danger_low=4,
                      category="GPS"),
    ChannelDefinition(id=506, name="GPS HDOP", units="", channel_type=ChannelType.GPS,
                      decimals=1, min_value=0, max_value=50, warning_high=2.0, danger_high=5.0,
                      category="GPS"),
]

# Lap Timer channels (550-599)
LAPTIMER_CHANNELS = [
    ChannelDefinition(id=550, name="Current Lap Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=600, category="Lap Timer"),
    ChannelDefinition(id=551, name="Last Lap Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=600, category="Lap Timer"),
    ChannelDefinition(id=552, name="Best Lap Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=600, category="Lap Timer"),
    ChannelDefinition(id=553, name="Delta", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=-60, max_value=60, category="Lap Timer"),
    ChannelDefinition(id=554, name="Lap Number", units="", channel_type=ChannelType.LAPTIMER,
                      decimals=0, min_value=0, max_value=999, category="Lap Timer"),
    ChannelDefinition(id=555, name="Current Sector", units="", channel_type=ChannelType.LAPTIMER,
                      decimals=0, min_value=0, max_value=10, category="Lap Timer"),
    ChannelDefinition(id=556, name="Sector 1 Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=300, category="Lap Timer"),
    ChannelDefinition(id=557, name="Sector 2 Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=300, category="Lap Timer"),
    ChannelDefinition(id=558, name="Sector 3 Time", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=300, category="Lap Timer"),
    ChannelDefinition(id=559, name="Predicted Lap", units="s", channel_type=ChannelType.LAPTIMER,
                      decimals=3, min_value=0, max_value=600, category="Lap Timer"),
]

# Engine/ECU channels (100-199)
ENGINE_CHANNELS = [
    ChannelDefinition(id=100, name="Engine RPM", units="RPM", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=12000, warning_high=7500, danger_high=8500,
                      category="Engine", can_message_id=0x360, can_start_bit=0, can_bit_length=16),
    ChannelDefinition(id=101, name="Vehicle Speed", units="km/h", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=350, category="Engine",
                      can_message_id=0x360, can_start_bit=16, can_bit_length=16, can_scale=0.1),
    ChannelDefinition(id=102, name="Throttle Position", units="%", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=0, max_value=100, category="Engine",
                      can_message_id=0x361, can_start_bit=0, can_bit_length=8, can_scale=0.5),
    ChannelDefinition(id=103, name="Coolant Temp", units="°C", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=-40, max_value=150, warning_high=105, danger_high=115,
                      category="Engine", can_message_id=0x362, can_start_bit=0, can_bit_length=8, can_offset=-40),
    ChannelDefinition(id=104, name="Oil Temp", units="°C", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=-40, max_value=180, warning_high=130, danger_high=145,
                      category="Engine", can_message_id=0x362, can_start_bit=8, can_bit_length=8, can_offset=-40),
    ChannelDefinition(id=105, name="Oil Pressure", units="bar", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=0, max_value=10, warning_low=1.5, danger_low=0.8,
                      category="Engine", can_message_id=0x363, can_start_bit=0, can_bit_length=8, can_scale=0.1),
    ChannelDefinition(id=106, name="Fuel Pressure", units="bar", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=0, max_value=10, warning_low=2.5, danger_low=2.0,
                      category="Engine", can_message_id=0x363, can_start_bit=8, can_bit_length=8, can_scale=0.1),
    ChannelDefinition(id=107, name="Boost Pressure", units="bar", channel_type=ChannelType.CAN_RX,
                      decimals=2, min_value=-1, max_value=3, category="Engine",
                      can_message_id=0x364, can_start_bit=0, can_bit_length=16,
                      can_data_type=CANDataType.SIGNED, can_scale=0.01),
    ChannelDefinition(id=108, name="AFR", units="λ", channel_type=ChannelType.CAN_RX,
                      decimals=2, min_value=0.6, max_value=1.4, warning_low=0.75, warning_high=1.15,
                      category="Engine", can_message_id=0x365, can_start_bit=0, can_bit_length=8, can_scale=0.01, can_offset=0.5),
    ChannelDefinition(id=109, name="Ignition Advance", units="°", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=-10, max_value=60, category="Engine",
                      can_message_id=0x365, can_start_bit=8, can_bit_length=8,
                      can_data_type=CANDataType.SIGNED, can_scale=0.5),
    ChannelDefinition(id=110, name="Gear", units="", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=8, category="Engine",
                      can_message_id=0x366, can_start_bit=0, can_bit_length=4),
    ChannelDefinition(id=111, name="Fuel Level", units="%", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=100, warning_low=15, danger_low=5,
                      category="Engine", can_message_id=0x366, can_start_bit=8, can_bit_length=8),
    ChannelDefinition(id=112, name="Battery Voltage", units="V", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=0, max_value=20, warning_low=12.0, danger_low=11.0,
                      category="Engine", can_message_id=0x367, can_start_bit=0, can_bit_length=8, can_scale=0.1),
    ChannelDefinition(id=113, name="IAT", units="°C", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=-40, max_value=100, warning_high=50, danger_high=60,
                      category="Engine", can_message_id=0x362, can_start_bit=16, can_bit_length=8, can_offset=-40),
    ChannelDefinition(id=114, name="MAP", units="kPa", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=400, category="Engine",
                      can_message_id=0x364, can_start_bit=16, can_bit_length=16),
    ChannelDefinition(id=115, name="EGT 1", units="°C", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=1100, warning_high=900, danger_high=1000,
                      category="Engine", can_message_id=0x368, can_start_bit=0, can_bit_length=16),
    ChannelDefinition(id=116, name="EGT 2", units="°C", channel_type=ChannelType.CAN_RX,
                      decimals=0, min_value=0, max_value=1100, warning_high=900, danger_high=1000,
                      category="Engine", can_message_id=0x368, can_start_bit=16, can_bit_length=16),
    ChannelDefinition(id=117, name="Brake Pressure", units="bar", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=0, max_value=200, category="Chassis",
                      can_message_id=0x370, can_start_bit=0, can_bit_length=16, can_scale=0.1),
    ChannelDefinition(id=118, name="Steering Angle", units="°", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=-540, max_value=540, category="Chassis",
                      can_message_id=0x371, can_start_bit=0, can_bit_length=16,
                      can_data_type=CANDataType.SIGNED, can_scale=0.1),
]

# Wheel speed channels (119-122)
WHEEL_CHANNELS = [
    ChannelDefinition(id=119, name="Wheel Speed FL", units="km/h", channel_type=ChannelType.DIGITAL,
                      decimals=1, min_value=0, max_value=350, category="Chassis",
                      digital_input_type=DigitalInputType.SPEED, digital_channel=0, pulses_per_unit=4.0),
    ChannelDefinition(id=120, name="Wheel Speed FR", units="km/h", channel_type=ChannelType.DIGITAL,
                      decimals=1, min_value=0, max_value=350, category="Chassis",
                      digital_input_type=DigitalInputType.SPEED, digital_channel=1, pulses_per_unit=4.0),
    ChannelDefinition(id=121, name="Wheel Speed RL", units="km/h", channel_type=ChannelType.DIGITAL,
                      decimals=1, min_value=0, max_value=350, category="Chassis",
                      digital_input_type=DigitalInputType.SPEED, digital_channel=2, pulses_per_unit=4.0),
    ChannelDefinition(id=122, name="Wheel Speed RR", units="km/h", channel_type=ChannelType.DIGITAL,
                      decimals=1, min_value=0, max_value=350, category="Chassis",
                      digital_input_type=DigitalInputType.SPEED, digital_channel=3, pulses_per_unit=4.0),
]

# G-force channels (123-125)
GFORCE_CHANNELS = [
    ChannelDefinition(id=123, name="G Lateral", units="g", channel_type=ChannelType.CAN_RX,
                      decimals=2, min_value=-3, max_value=3, category="Chassis",
                      can_message_id=0x372, can_start_bit=0, can_bit_length=16,
                      can_data_type=CANDataType.SIGNED, can_scale=0.001),
    ChannelDefinition(id=124, name="G Longitudinal", units="g", channel_type=ChannelType.CAN_RX,
                      decimals=2, min_value=-3, max_value=3, category="Chassis",
                      can_message_id=0x372, can_start_bit=16, can_bit_length=16,
                      can_data_type=CANDataType.SIGNED, can_scale=0.001),
    ChannelDefinition(id=125, name="Yaw Rate", units="°/s", channel_type=ChannelType.CAN_RX,
                      decimals=1, min_value=-200, max_value=200, category="Chassis",
                      can_message_id=0x372, can_start_bit=32, can_bit_length=16,
                      can_data_type=CANDataType.SIGNED, can_scale=0.01),
]

# Analog sensor channels (200-207)
ANALOG_CHANNELS = [
    ChannelDefinition(id=200, name="Analog In 1", units="V", channel_type=ChannelType.ANALOG,
                      decimals=2, min_value=0, max_value=5, category="Analog Inputs",
                      analog_input_type=AnalogInputType.VOLTAGE, analog_channel=0),
    ChannelDefinition(id=201, name="Analog In 2", units="V", channel_type=ChannelType.ANALOG,
                      decimals=2, min_value=0, max_value=5, category="Analog Inputs",
                      analog_input_type=AnalogInputType.VOLTAGE, analog_channel=1),
    ChannelDefinition(id=202, name="Analog In 3", units="V", channel_type=ChannelType.ANALOG,
                      decimals=2, min_value=0, max_value=5, category="Analog Inputs",
                      analog_input_type=AnalogInputType.VOLTAGE, analog_channel=2),
    ChannelDefinition(id=203, name="Analog In 4", units="V", channel_type=ChannelType.ANALOG,
                      decimals=2, min_value=0, max_value=5, category="Analog Inputs",
                      analog_input_type=AnalogInputType.VOLTAGE, analog_channel=3),
    ChannelDefinition(id=204, name="Oil Temp Sensor", units="°C", channel_type=ChannelType.ANALOG,
                      decimals=0, min_value=-40, max_value=180, warning_high=130, danger_high=145,
                      category="Analog Inputs", analog_input_type=AnalogInputType.THERMISTOR_NTC,
                      analog_channel=4, thermistor_beta=3950, thermistor_r25=10000, thermistor_pullup=2200),
    ChannelDefinition(id=205, name="Oil Pressure Sensor", units="bar", channel_type=ChannelType.ANALOG,
                      decimals=1, min_value=0, max_value=10, warning_low=1.5, danger_low=0.8,
                      category="Analog Inputs", analog_input_type=AnalogInputType.VOLTAGE,
                      analog_channel=5, analog_scale=2.5, analog_offset=-1.25),
    ChannelDefinition(id=206, name="Fuel Pressure Sensor", units="bar", channel_type=ChannelType.ANALOG,
                      decimals=1, min_value=0, max_value=10, warning_low=2.5, danger_low=2.0,
                      category="Analog Inputs", analog_input_type=AnalogInputType.VOLTAGE,
                      analog_channel=6, analog_scale=2.5, analog_offset=-1.25),
    ChannelDefinition(id=207, name="Brake Pressure Sensor", units="bar", channel_type=ChannelType.ANALOG,
                      decimals=0, min_value=0, max_value=200, category="Analog Inputs",
                      analog_input_type=AnalogInputType.VOLTAGE, analog_channel=7,
                      analog_scale=50, analog_offset=0),
]


def get_all_predefined_channels() -> List[ChannelDefinition]:
    """Get all predefined channels."""
    return (
        SYSTEM_CHANNELS +
        GPS_CHANNELS +
        LAPTIMER_CHANNELS +
        ENGINE_CHANNELS +
        WHEEL_CHANNELS +
        GFORCE_CHANNELS +
        ANALOG_CHANNELS
    )


def get_channels_by_category() -> Dict[str, List[ChannelDefinition]]:
    """Get channels grouped by category."""
    channels = get_all_predefined_channels()
    result: Dict[str, List[ChannelDefinition]] = {}

    for channel in channels:
        if channel.category not in result:
            result[channel.category] = []
        result[channel.category].append(channel)

    return result


def get_channel_by_id(channel_id: int) -> Optional[ChannelDefinition]:
    """Get channel by ID."""
    for channel in get_all_predefined_channels():
        if channel.id == channel_id:
            return channel
    return None


def get_channel_by_name(name: str) -> Optional[ChannelDefinition]:
    """Get channel by name."""
    for channel in get_all_predefined_channels():
        if channel.name == name:
            return channel
    return None
