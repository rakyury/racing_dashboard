# Emulator Transport
"""Emulator transport for development without hardware."""

import logging
import time
import random
import struct
import threading
from typing import Optional, List, Dict, Any

from .transport_base import TransportBase, TransportState, TransportInfo
from .protocol import (
    Protocol, ProtocolFrame, MessageType, ErrorCode,
    encode_frame, CHUNK_SIZE
)

logger = logging.getLogger(__name__)


class EmulatorTransport(TransportBase):
    """
    Emulated transport for development and testing.
    Simulates a Racing Dashboard device with telemetry.
    """

    def __init__(self):
        super().__init__()
        self._running = False
        self._telemetry_thread: Optional[threading.Thread] = None
        self._telemetry_rate_hz = 0
        self._tx_queue: List[bytes] = []
        self._rx_buffer = bytearray()
        self._lock = threading.Lock()

        # Simulated device state
        self._device_info = {
            "firmware_version": "2.0.0-emu",
            "serial_number": "EMU-12345",
            "hardware_version": "v1.0",
        }

        # Simulated telemetry values
        self._telemetry = {
            "rpm": 3500,
            "speed_kmh": 0,
            "gear": 0,
            "throttle_percent": 0,
            "brake_percent": 0,
            "coolant_temp_c": 85,
            "oil_temp_c": 90,
            "fuel_level_percent": 75,
            "g_lateral": 0.0,
            "g_longitudinal": 0.0,
            "lap_time_ms": 0,
        }

        # Simulation parameters
        self._sim_time = 0.0
        self._lap_start_time = 0.0

        # Configuration storage
        self._config_data: bytes = b'{}'

    def connect(self, **kwargs) -> bool:
        """Connect to the emulator."""
        if self._state == TransportState.CONNECTED:
            return True

        logger.info("Connecting to emulator")
        self._set_state(TransportState.CONNECTING)

        # Simulate connection delay
        time.sleep(0.2)

        self._running = True
        self._set_state(TransportState.CONNECTED)
        logger.info("Emulator connected")
        return True

    def disconnect(self) -> None:
        """Disconnect from the emulator."""
        if self._state == TransportState.DISCONNECTED:
            return

        logger.info("Disconnecting emulator")
        self._running = False

        # Stop telemetry thread
        if self._telemetry_thread and self._telemetry_thread.is_alive():
            self._telemetry_rate_hz = 0
            self._telemetry_thread.join(timeout=1.0)

        self._set_state(TransportState.DISCONNECTED)
        logger.info("Emulator disconnected")

    def send(self, data: bytes) -> bool:
        """
        Send data to the emulator.
        The emulator processes the data and generates responses.
        """
        if not self.is_connected:
            return False

        # Decode and process frames
        protocol = Protocol()
        frames = protocol.feed_data(data)

        for frame in frames:
            self._process_frame(frame)

        return True

    def receive(self, timeout: float = 1.0) -> Optional[bytes]:
        """Receive data from the emulator."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._lock:
                if self._rx_buffer:
                    data = bytes(self._rx_buffer)
                    self._rx_buffer.clear()
                    return data
            time.sleep(0.01)

        return None

    def _process_frame(self, frame: ProtocolFrame) -> None:
        """Process a received frame and generate response."""
        response_frames = []

        if frame.message_type == MessageType.PING:
            # Respond with PONG
            response = ProtocolFrame(MessageType.PONG, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.GET_INFO:
            # Send device info
            payload = self._encode_device_info()
            response = ProtocolFrame(MessageType.INFO_RESPONSE, payload, frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.GET_CONFIG:
            # Send configuration in chunks
            response_frames.extend(self._create_config_response(frame.sequence))

        elif frame.message_type == MessageType.CONFIG_CHUNK:
            # Receive configuration chunk
            self._process_config_chunk(frame.payload)
            response = ProtocolFrame(MessageType.CONFIG_CHUNK_ACK, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.SUBSCRIBE_TELEMETRY:
            # Start telemetry streaming
            rate_hz = struct.unpack('<H', frame.payload)[0] if frame.payload else 50
            self._start_telemetry(rate_hz)
            response = ProtocolFrame(MessageType.ACK, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.UNSUBSCRIBE_TELEMETRY:
            # Stop telemetry streaming
            self._stop_telemetry()
            response = ProtocolFrame(MessageType.ACK, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.SET_CHANNEL:
            # Set channel value
            channel_id, value = struct.unpack('<HI', frame.payload)
            logger.debug(f"Set channel {channel_id} = {value}")
            response = ProtocolFrame(MessageType.CHANNEL_ACK, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.SAVE_TO_FLASH:
            # Simulate save
            time.sleep(0.1)
            response = ProtocolFrame(MessageType.ACK, b"", frame.sequence)
            response_frames.append(response)

        elif frame.message_type == MessageType.RESTART_DEVICE:
            # Simulate restart
            logger.info("Emulator: Simulating device restart")
            self._stop_telemetry()
            response = ProtocolFrame(MessageType.ACK, b"", frame.sequence)
            response_frames.append(response)

        # Encode and queue responses
        for resp in response_frames:
            encoded = encode_frame(resp)
            with self._lock:
                self._rx_buffer.extend(encoded)
            self._on_data_received(encoded)

    def _encode_device_info(self) -> bytes:
        """Encode device info response."""
        fw = self._device_info["firmware_version"].encode('utf-8')[:16].ljust(16, b'\x00')
        serial = self._device_info["serial_number"].encode('utf-8')[:16].ljust(16, b'\x00')
        hw = self._device_info["hardware_version"].encode('utf-8')[:8].ljust(8, b'\x00')
        return fw + serial + hw

    def _create_config_response(self, sequence: int) -> List[ProtocolFrame]:
        """Create config response frames."""
        frames = []
        data = self._config_data

        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE or 1

        for i in range(total_chunks):
            chunk_start = i * CHUNK_SIZE
            chunk_end = min((i + 1) * CHUNK_SIZE, len(data))
            chunk_data = data[chunk_start:chunk_end]

            # Chunk header: chunk_idx (2), total_chunks (2), compressed (1)
            header = struct.pack('<HHB', i, total_chunks, 0)
            payload = header + chunk_data

            frame = ProtocolFrame(MessageType.CONFIG_CHUNK, payload, sequence)
            frames.append(frame)

        return frames

    def _process_config_chunk(self, payload: bytes) -> None:
        """Process received config chunk."""
        # For simplicity, just store directly
        # Real implementation would reassemble chunks
        if len(payload) > 5:
            chunk_data = payload[5:]
            # Just store the last chunk for now
            self._config_data = chunk_data

    def _start_telemetry(self, rate_hz: int) -> None:
        """Start telemetry streaming."""
        self._telemetry_rate_hz = rate_hz
        if self._telemetry_thread is None or not self._telemetry_thread.is_alive():
            self._telemetry_thread = threading.Thread(
                target=self._telemetry_loop, daemon=True
            )
            self._telemetry_thread.start()

    def _stop_telemetry(self) -> None:
        """Stop telemetry streaming."""
        self._telemetry_rate_hz = 0

    def _telemetry_loop(self) -> None:
        """Background thread for telemetry generation."""
        last_time = time.time()

        while self._running:
            if self._telemetry_rate_hz <= 0:
                time.sleep(0.1)
                continue

            interval = 1.0 / self._telemetry_rate_hz
            current_time = time.time()

            if current_time - last_time >= interval:
                self._update_simulation(current_time - last_time)
                self._send_telemetry()
                last_time = current_time
            else:
                time.sleep(0.001)

    def _update_simulation(self, dt: float) -> None:
        """Update simulated telemetry values."""
        self._sim_time += dt

        # Simulate engine behavior
        base_rpm = 3500 + 2000 * (0.5 + 0.5 * time.time() % 1)
        self._telemetry["rpm"] = int(base_rpm + random.uniform(-50, 50))

        # Simulate speed (follows RPM roughly)
        target_speed = (self._telemetry["rpm"] - 1000) / 50
        current_speed = self._telemetry["speed_kmh"]
        self._telemetry["speed_kmh"] = int(
            current_speed + (target_speed - current_speed) * 0.1
        )

        # Simulate gear based on speed
        speed = self._telemetry["speed_kmh"]
        if speed < 20:
            gear = 1
        elif speed < 40:
            gear = 2
        elif speed < 70:
            gear = 3
        elif speed < 100:
            gear = 4
        elif speed < 140:
            gear = 5
        else:
            gear = 6
        self._telemetry["gear"] = gear

        # Simulate throttle and brake (oscillating)
        phase = (self._sim_time % 10) / 10  # 10 second cycle
        if phase < 0.6:  # Accelerating
            self._telemetry["throttle_percent"] = int(60 + 40 * phase)
            self._telemetry["brake_percent"] = 0
        else:  # Braking
            self._telemetry["throttle_percent"] = 0
            self._telemetry["brake_percent"] = int(100 * (1 - (phase - 0.6) / 0.4))

        # Simulate temperatures (slowly varying)
        self._telemetry["coolant_temp_c"] = 85 + int(5 * (0.5 + 0.5 * (time.time() % 60) / 60))
        self._telemetry["oil_temp_c"] = 90 + int(8 * (0.5 + 0.5 * (time.time() % 120) / 120))

        # Simulate G-forces
        self._telemetry["g_lateral"] = 0.5 * (random.random() * 2 - 1)
        if self._telemetry["brake_percent"] > 50:
            self._telemetry["g_longitudinal"] = -1.2 * (self._telemetry["brake_percent"] / 100)
        else:
            self._telemetry["g_longitudinal"] = 0.3 * (self._telemetry["throttle_percent"] / 100)

        # Simulate lap time
        self._telemetry["lap_time_ms"] = int((self._sim_time - self._lap_start_time) * 1000) % 120000

    def _send_telemetry(self) -> None:
        """Send telemetry frame."""
        payload = struct.pack(
            '<IHHBBBbbBhhI',
            int(self._sim_time * 1000),  # timestamp_ms
            self._telemetry["rpm"],
            self._telemetry["speed_kmh"],
            self._telemetry["gear"],
            self._telemetry["throttle_percent"],
            self._telemetry["brake_percent"],
            self._telemetry["coolant_temp_c"],
            self._telemetry["oil_temp_c"],
            self._telemetry["fuel_level_percent"],
            int(self._telemetry["g_lateral"] * 100),
            int(self._telemetry["g_longitudinal"] * 100),
            self._telemetry["lap_time_ms"],
        )

        frame = ProtocolFrame(MessageType.TELEMETRY_DATA, payload, 0)
        encoded = encode_frame(frame)

        with self._lock:
            self._rx_buffer.extend(encoded)
        self._on_data_received(encoded)

    @staticmethod
    def list_ports() -> List[TransportInfo]:
        """List available emulator connections."""
        return [
            TransportInfo(
                port="emulator",
                description="Racing Dashboard Emulator",
                hardware_id="EMU",
                manufacturer="Emulator",
                is_racing_dashboard=True,
            )
        ]
