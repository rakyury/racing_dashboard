# ECU Presets
"""Predefined CAN configurations for popular ECUs."""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

from .can_database import CANDatabase, CANMessage, CANSignal, ByteOrder, ValueType


class ECUBrand(Enum):
    """ECU manufacturers."""
    HALTECH = "Haltech"
    AEM = "AEM"
    LINK = "Link"
    MOTEC = "MoTeC"
    MEGASQUIRT = "MegaSquirt"
    ECUMASTER = "ECUMaster"
    MAXXECU = "MaxxECU"
    SYVECS = "Syvecs"
    EMTRON = "Emtron"
    LIFE_RACING = "Life Racing"
    GENERIC = "Generic"


@dataclass
class ECUPreset:
    """ECU preset definition."""
    brand: ECUBrand
    model: str
    description: str
    can_speed: int  # kbps
    database: CANDatabase

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "brand": self.brand.value,
            "model": self.model,
            "description": self.description,
            "can_speed": self.can_speed,
            "database": self.database.to_dict(),
        }


# =============================================================================
# Haltech Presets
# =============================================================================

def create_haltech_elite_preset() -> ECUPreset:
    """Haltech Elite series CAN stream."""
    db = CANDatabase(name="Haltech Elite", version="1.0")

    # Frame 1 - Engine RPM, MAP, TPS, Coolant
    msg1 = CANMessage(id=0x360, name="Engine1", dlc=8, cycle_time_ms=10)
    msg1.add_signal(CANSignal(name="RPM", start_bit=0, bit_length=16, scale=1.0, unit="RPM", max_value=20000))
    msg1.add_signal(CANSignal(name="MAP", start_bit=16, bit_length=16, scale=0.1, unit="kPa", max_value=400))
    msg1.add_signal(CANSignal(name="TPS", start_bit=32, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg1.add_signal(CANSignal(name="Coolant_Temp", start_bit=48, bit_length=16, scale=0.1, offset=-273.15, unit="°C", min_value=-40, max_value=200))
    db.add_message(msg1)

    # Frame 2 - Air Temp, Fuel Pressure, Oil Pressure, Oil Temp
    msg2 = CANMessage(id=0x361, name="Engine2", dlc=8, cycle_time_ms=20)
    msg2.add_signal(CANSignal(name="Air_Temp", start_bit=0, bit_length=16, scale=0.1, offset=-273.15, unit="°C", min_value=-40, max_value=100))
    msg2.add_signal(CANSignal(name="Fuel_Pressure", start_bit=16, bit_length=16, scale=0.1, unit="kPa", max_value=1000))
    msg2.add_signal(CANSignal(name="Oil_Pressure", start_bit=32, bit_length=16, scale=0.1, unit="kPa", max_value=1000))
    msg2.add_signal(CANSignal(name="Oil_Temp", start_bit=48, bit_length=16, scale=0.1, offset=-273.15, unit="°C", min_value=-40, max_value=200))
    db.add_message(msg2)

    # Frame 3 - Fuel Composition, Ethanol Temp, Fuel Level, Voltage
    msg3 = CANMessage(id=0x362, name="Fuel", dlc=8, cycle_time_ms=100)
    msg3.add_signal(CANSignal(name="Ethanol_Content", start_bit=0, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg3.add_signal(CANSignal(name="Ethanol_Temp", start_bit=16, bit_length=16, scale=0.1, offset=-273.15, unit="°C", min_value=-40, max_value=100))
    msg3.add_signal(CANSignal(name="Fuel_Level", start_bit=32, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg3.add_signal(CANSignal(name="Battery_Voltage", start_bit=48, bit_length=16, scale=0.01, unit="V", max_value=20))
    db.add_message(msg3)

    # Frame 4 - Vehicle Speed, Gear, Lambda
    msg4 = CANMessage(id=0x363, name="Vehicle", dlc=8, cycle_time_ms=20)
    msg4.add_signal(CANSignal(name="Vehicle_Speed", start_bit=0, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    msg4.add_signal(CANSignal(name="Gear", start_bit=16, bit_length=8, scale=1.0, unit="", max_value=8))
    msg4.add_signal(CANSignal(name="Lambda_1", start_bit=32, bit_length=16, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    msg4.add_signal(CANSignal(name="Lambda_2", start_bit=48, bit_length=16, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    db.add_message(msg4)

    # Frame 5 - Ignition Timing, Boost Target, Boost Duty
    msg5 = CANMessage(id=0x364, name="Ignition", dlc=8, cycle_time_ms=20)
    msg5.add_signal(CANSignal(name="Ignition_Angle", start_bit=0, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°", min_value=-20, max_value=60))
    msg5.add_signal(CANSignal(name="Boost_Target", start_bit=16, bit_length=16, scale=0.1, unit="kPa", max_value=400))
    msg5.add_signal(CANSignal(name="Boost_Duty", start_bit=32, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg5.add_signal(CANSignal(name="Knock_Level", start_bit=48, bit_length=16, scale=0.1, unit="", max_value=100))
    db.add_message(msg5)

    # Frame 6 - Wheel Speeds
    msg6 = CANMessage(id=0x370, name="WheelSpeed", dlc=8, cycle_time_ms=20)
    msg6.add_signal(CANSignal(name="Wheel_FL", start_bit=0, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    msg6.add_signal(CANSignal(name="Wheel_FR", start_bit=16, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    msg6.add_signal(CANSignal(name="Wheel_RL", start_bit=32, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    msg6.add_signal(CANSignal(name="Wheel_RR", start_bit=48, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    db.add_message(msg6)

    return ECUPreset(
        brand=ECUBrand.HALTECH,
        model="Elite Series",
        description="Haltech Elite 1500/2500 CAN Stream",
        can_speed=1000,
        database=db
    )


# =============================================================================
# AEM Presets
# =============================================================================

def create_aem_infinity_preset() -> ECUPreset:
    """AEM Infinity CAN broadcast."""
    db = CANDatabase(name="AEM Infinity", version="1.0")

    # Standard AEM CAN IDs start at 0x1F0A000
    # Simplified version with typical dash stream

    msg1 = CANMessage(id=0x1F0A000, name="Engine1", dlc=8, extended=True, cycle_time_ms=10)
    msg1.add_signal(CANSignal(name="RPM", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, unit="RPM", max_value=15000))
    msg1.add_signal(CANSignal(name="Engine_Load", start_bit=16, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, unit="%", max_value=200))
    msg1.add_signal(CANSignal(name="Throttle", start_bit=32, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, unit="%", max_value=100))
    msg1.add_signal(CANSignal(name="Coolant", start_bit=48, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, offset=-273.15, unit="°C"))
    db.add_message(msg1)

    msg2 = CANMessage(id=0x1F0A001, name="Engine2", dlc=8, extended=True, cycle_time_ms=10)
    msg2.add_signal(CANSignal(name="MAP", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, unit="kPa", max_value=400))
    msg2.add_signal(CANSignal(name="IAT", start_bit=16, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, offset=-273.15, unit="°C"))
    msg2.add_signal(CANSignal(name="Battery", start_bit=32, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.01, unit="V", max_value=20))
    msg2.add_signal(CANSignal(name="Gear", start_bit=48, bit_length=8, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, max_value=8))
    db.add_message(msg2)

    msg3 = CANMessage(id=0x1F0A002, name="Lambda", dlc=8, extended=True, cycle_time_ms=20)
    msg3.add_signal(CANSignal(name="Lambda_1", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    msg3.add_signal(CANSignal(name="Lambda_2", start_bit=16, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    msg3.add_signal(CANSignal(name="AFR_Target", start_bit=32, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    db.add_message(msg3)

    return ECUPreset(
        brand=ECUBrand.AEM,
        model="Infinity",
        description="AEM Infinity ECU CAN Broadcast",
        can_speed=1000,
        database=db
    )


# =============================================================================
# Link Presets
# =============================================================================

def create_link_g4_preset() -> ECUPreset:
    """Link G4/G4+ CAN stream."""
    db = CANDatabase(name="Link G4+", version="1.0")

    # Generic Dash Stream
    msg1 = CANMessage(id=0x3E0, name="Dash1", dlc=8, cycle_time_ms=20)
    msg1.add_signal(CANSignal(name="RPM", start_bit=0, bit_length=16, scale=1.0, unit="RPM", max_value=15000))
    msg1.add_signal(CANSignal(name="MAP", start_bit=16, bit_length=16, scale=0.1, unit="kPa", max_value=400))
    msg1.add_signal(CANSignal(name="MGP", start_bit=32, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="kPa", min_value=-100, max_value=300))
    msg1.add_signal(CANSignal(name="Baro", start_bit=48, bit_length=16, scale=0.1, unit="kPa", max_value=120))
    db.add_message(msg1)

    msg2 = CANMessage(id=0x3E1, name="Dash2", dlc=8, cycle_time_ms=20)
    msg2.add_signal(CANSignal(name="TPS", start_bit=0, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg2.add_signal(CANSignal(name="Inj_Duty", start_bit=16, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg2.add_signal(CANSignal(name="Inj_DC_Stg2", start_bit=32, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg2.add_signal(CANSignal(name="Ign_Angle", start_bit=48, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°", min_value=-20, max_value=60))
    db.add_message(msg2)

    msg3 = CANMessage(id=0x3E2, name="Dash3", dlc=8, cycle_time_ms=50)
    msg3.add_signal(CANSignal(name="Coolant", start_bit=0, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°C", min_value=-40, max_value=200))
    msg3.add_signal(CANSignal(name="IAT", start_bit=16, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°C", min_value=-40, max_value=100))
    msg3.add_signal(CANSignal(name="Battery", start_bit=32, bit_length=16, scale=0.01, unit="V", max_value=20))
    msg3.add_signal(CANSignal(name="Speed", start_bit=48, bit_length=16, scale=0.1, unit="km/h", max_value=400))
    db.add_message(msg3)

    msg4 = CANMessage(id=0x3E3, name="Dash4", dlc=8, cycle_time_ms=50)
    msg4.add_signal(CANSignal(name="Lambda_1", start_bit=0, bit_length=16, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    msg4.add_signal(CANSignal(name="Lambda_2", start_bit=16, bit_length=16, scale=0.001, unit="λ", min_value=0.5, max_value=2.0))
    msg4.add_signal(CANSignal(name="Oil_Temp", start_bit=32, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°C", min_value=-40, max_value=200))
    msg4.add_signal(CANSignal(name="Oil_Press", start_bit=48, bit_length=16, scale=0.1, unit="kPa", max_value=1000))
    db.add_message(msg4)

    msg5 = CANMessage(id=0x3E4, name="Dash5", dlc=8, cycle_time_ms=100)
    msg5.add_signal(CANSignal(name="Fuel_Press", start_bit=0, bit_length=16, scale=0.1, unit="kPa", max_value=1000))
    msg5.add_signal(CANSignal(name="Ethanol", start_bit=16, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg5.add_signal(CANSignal(name="Gear", start_bit=32, bit_length=8, scale=1.0, max_value=8))
    msg5.add_signal(CANSignal(name="Fuel_Level", start_bit=40, bit_length=16, scale=0.1, unit="%", max_value=100))
    db.add_message(msg5)

    return ECUPreset(
        brand=ECUBrand.LINK,
        model="G4+/G4X",
        description="Link G4+/G4X Generic Dash Stream",
        can_speed=1000,
        database=db
    )


# =============================================================================
# MegaSquirt Presets
# =============================================================================

def create_megasquirt_preset() -> ECUPreset:
    """MegaSquirt 3 CAN broadcast."""
    db = CANDatabase(name="MegaSquirt 3", version="1.0")

    # MS3 Dash Broadcast
    msg1 = CANMessage(id=0x5F0, name="MS_Dash1", dlc=8, cycle_time_ms=20)
    msg1.add_signal(CANSignal(name="RPM", start_bit=0, bit_length=16, scale=1.0, unit="RPM", max_value=15000))
    msg1.add_signal(CANSignal(name="CLT", start_bit=16, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°F", min_value=-40, max_value=300))
    msg1.add_signal(CANSignal(name="TPS", start_bit=32, bit_length=16, scale=0.1, unit="%", max_value=100))
    msg1.add_signal(CANSignal(name="MAP", start_bit=48, bit_length=16, scale=0.1, unit="kPa", max_value=400))
    db.add_message(msg1)

    msg2 = CANMessage(id=0x5F1, name="MS_Dash2", dlc=8, cycle_time_ms=20)
    msg2.add_signal(CANSignal(name="MAT", start_bit=0, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°F", min_value=-40, max_value=300))
    msg2.add_signal(CANSignal(name="ADV", start_bit=16, bit_length=16, scale=0.1, value_type=ValueType.SIGNED, unit="°", min_value=-20, max_value=60))
    msg2.add_signal(CANSignal(name="AFR", start_bit=32, bit_length=8, scale=0.1, unit="AFR", min_value=9, max_value=20))
    msg2.add_signal(CANSignal(name="EGO_Corr", start_bit=40, bit_length=16, scale=0.1, unit="%", max_value=200))
    db.add_message(msg2)

    msg3 = CANMessage(id=0x5F2, name="MS_Dash3", dlc=8, cycle_time_ms=50)
    msg3.add_signal(CANSignal(name="Batt_V", start_bit=0, bit_length=16, scale=0.1, unit="V", max_value=20))
    msg3.add_signal(CANSignal(name="PW1", start_bit=16, bit_length=16, scale=0.001, unit="ms", max_value=50))
    msg3.add_signal(CANSignal(name="VSS", start_bit=32, bit_length=16, scale=0.1, unit="mph", max_value=200))
    msg3.add_signal(CANSignal(name="Gear", start_bit=48, bit_length=8, scale=1.0, max_value=8))
    db.add_message(msg3)

    return ECUPreset(
        brand=ECUBrand.MEGASQUIRT,
        model="MS3/MS3-Pro",
        description="MegaSquirt 3 CAN Broadcast",
        can_speed=500,
        database=db
    )


# =============================================================================
# ECUMaster Presets
# =============================================================================

def create_ecumaster_emu_preset() -> ECUPreset:
    """ECUMaster EMU CAN stream."""
    db = CANDatabase(name="ECUMaster EMU", version="1.0")

    msg1 = CANMessage(id=0x600, name="EMU_Stream1", dlc=8, cycle_time_ms=10)
    msg1.add_signal(CANSignal(name="RPM", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, unit="RPM", max_value=15000))
    msg1.add_signal(CANSignal(name="TPS", start_bit=16, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, unit="%", max_value=100))
    msg1.add_signal(CANSignal(name="IAT", start_bit=32, bit_length=8, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, offset=-40, unit="°C"))
    msg1.add_signal(CANSignal(name="CLT", start_bit=40, bit_length=8, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, offset=-40, unit="°C"))
    db.add_message(msg1)

    msg2 = CANMessage(id=0x601, name="EMU_Stream2", dlc=8, cycle_time_ms=10)
    msg2.add_signal(CANSignal(name="MAP", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, unit="kPa", max_value=400))
    msg2.add_signal(CANSignal(name="Lambda", start_bit=16, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.001, unit="λ", max_value=2.0))
    msg2.add_signal(CANSignal(name="Speed", start_bit=32, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, unit="km/h", max_value=400))
    msg2.add_signal(CANSignal(name="Oil_Press", start_bit=48, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.0625, unit="bar", max_value=15))
    db.add_message(msg2)

    msg3 = CANMessage(id=0x602, name="EMU_Stream3", dlc=8, cycle_time_ms=20)
    msg3.add_signal(CANSignal(name="Fuel_Press", start_bit=0, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.0625, unit="bar", max_value=10))
    msg3.add_signal(CANSignal(name="Oil_Temp", start_bit=16, bit_length=8, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, offset=-40, unit="°C"))
    msg3.add_signal(CANSignal(name="Battery", start_bit=24, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.01, unit="V", max_value=20))
    msg3.add_signal(CANSignal(name="Gear", start_bit=40, bit_length=8, byte_order=ByteOrder.LITTLE_ENDIAN, scale=1.0, max_value=8))
    msg3.add_signal(CANSignal(name="Ign_Angle", start_bit=48, bit_length=16, byte_order=ByteOrder.LITTLE_ENDIAN, scale=0.1, value_type=ValueType.SIGNED, unit="°"))
    db.add_message(msg3)

    return ECUPreset(
        brand=ECUBrand.ECUMASTER,
        model="EMU Black/Classic",
        description="ECUMaster EMU CAN Stream",
        can_speed=1000,
        database=db
    )


# =============================================================================
# Generic OBD-II Preset
# =============================================================================

def create_obd2_preset() -> ECUPreset:
    """Generic OBD-II PIDs."""
    db = CANDatabase(name="OBD-II", version="1.0")

    # OBD-II responses come on 0x7E8-0x7EF
    msg1 = CANMessage(id=0x7E8, name="OBD_Response", dlc=8, cycle_time_ms=0)
    msg1.comment = "OBD-II ECU Response - decode based on PID"
    db.add_message(msg1)

    return ECUPreset(
        brand=ECUBrand.GENERIC,
        model="OBD-II",
        description="Generic OBD-II Protocol (requires polling)",
        can_speed=500,
        database=db
    )


# =============================================================================
# Preset Registry
# =============================================================================

def get_all_presets() -> List[ECUPreset]:
    """Get all available ECU presets."""
    return [
        create_haltech_elite_preset(),
        create_aem_infinity_preset(),
        create_link_g4_preset(),
        create_megasquirt_preset(),
        create_ecumaster_emu_preset(),
        create_obd2_preset(),
    ]


def get_presets_by_brand() -> Dict[ECUBrand, List[ECUPreset]]:
    """Get presets grouped by brand."""
    result: Dict[ECUBrand, List[ECUPreset]] = {}
    for preset in get_all_presets():
        if preset.brand not in result:
            result[preset.brand] = []
        result[preset.brand].append(preset)
    return result


def get_preset_by_name(brand: str, model: str) -> ECUPreset | None:
    """Get preset by brand and model name."""
    for preset in get_all_presets():
        if preset.brand.value == brand and preset.model == model:
            return preset
    return None
