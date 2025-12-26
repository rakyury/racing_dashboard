# Preview Simulator
"""Simulates live data for dashboard preview."""

import math
import random
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class SimulationMode(Enum):
    """Simulation mode presets."""
    IDLE = "idle"
    STREET = "street"
    TRACK_WARMUP = "track_warmup"
    TRACK_HOTLAP = "track_hotlap"
    DRAG_LAUNCH = "drag_launch"
    CUSTOM = "custom"


@dataclass
class ChannelSimConfig:
    """Configuration for simulating a channel."""
    channel_id: int
    base_value: float = 0.0
    amplitude: float = 0.0
    frequency: float = 1.0  # Hz
    noise: float = 0.0
    min_value: float = 0.0
    max_value: float = 100.0


class DataSimulator(QObject):
    """Simulates data channels for preview mode."""

    data_updated = pyqtSignal(dict)  # {channel_id: value}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._running = False
        self._time = 0.0
        self._dt = 0.05  # 20Hz update rate

        self._mode = SimulationMode.IDLE
        self._channel_values: Dict[int, float] = {}
        self._channel_configs: Dict[int, ChannelSimConfig] = {}

        # State variables for complex simulations
        self._rpm = 800
        self._speed = 0
        self._gear = 1
        self._throttle = 0
        self._lap_time = 0
        self._lap_number = 0
        self._best_lap = 0
        self._in_corner = False

        self._setup_default_configs()

    def _setup_default_configs(self) -> None:
        """Setup default channel configurations."""
        # RPM
        self._channel_configs[100] = ChannelSimConfig(100, 800, 0, 0, 50, 0, 9000)
        # Speed
        self._channel_configs[101] = ChannelSimConfig(101, 0, 0, 0, 2, 0, 300)
        # Throttle
        self._channel_configs[102] = ChannelSimConfig(102, 0, 0, 0, 0, 0, 100)
        # Coolant temp
        self._channel_configs[103] = ChannelSimConfig(103, 85, 5, 0.02, 1, 60, 120)
        # Oil temp
        self._channel_configs[104] = ChannelSimConfig(104, 90, 8, 0.015, 1, 60, 150)
        # Oil pressure
        self._channel_configs[105] = ChannelSimConfig(105, 4.0, 0.5, 0.5, 0.1, 0.5, 8)
        # Fuel pressure
        self._channel_configs[106] = ChannelSimConfig(106, 3.5, 0.2, 0.3, 0.05, 2, 5)
        # Boost
        self._channel_configs[107] = ChannelSimConfig(107, 0, 0, 0, 0.02, -1, 2.5)
        # AFR
        self._channel_configs[108] = ChannelSimConfig(108, 1.0, 0.05, 2, 0.02, 0.7, 1.3)
        # Gear
        self._channel_configs[110] = ChannelSimConfig(110, 1, 0, 0, 0, 0, 6)
        # Fuel level
        self._channel_configs[111] = ChannelSimConfig(111, 75, 0, 0, 0, 0, 100)
        # Battery
        self._channel_configs[112] = ChannelSimConfig(112, 13.8, 0.2, 0.1, 0.05, 11, 15)
        # IAT
        self._channel_configs[113] = ChannelSimConfig(113, 35, 3, 0.05, 1, 20, 60)
        # Brake pressure
        self._channel_configs[117] = ChannelSimConfig(117, 0, 0, 0, 0, 0, 150)
        # G lateral
        self._channel_configs[123] = ChannelSimConfig(123, 0, 0.2, 0.5, 0.05, -2, 2)
        # G longitudinal
        self._channel_configs[124] = ChannelSimConfig(124, 0, 0.1, 0.3, 0.02, -2, 2)

        # GPS
        self._channel_configs[503] = ChannelSimConfig(503, 0, 0, 0, 1, 0, 300)  # GPS Speed

        # Lap timer
        self._channel_configs[550] = ChannelSimConfig(550, 0, 0, 0, 0, 0, 600)  # Current lap time
        self._channel_configs[551] = ChannelSimConfig(551, 0, 0, 0, 0, 0, 600)  # Last lap
        self._channel_configs[552] = ChannelSimConfig(552, 0, 0, 0, 0, 0, 600)  # Best lap
        self._channel_configs[553] = ChannelSimConfig(553, 0, 0, 0, 0, -60, 60)  # Delta
        self._channel_configs[554] = ChannelSimConfig(554, 0, 0, 0, 0, 0, 999)  # Lap number

    def start(self) -> None:
        """Start simulation."""
        self._running = True
        self._time = 0.0
        self._timer.start(int(self._dt * 1000))

    def stop(self) -> None:
        """Stop simulation."""
        self._running = False
        self._timer.stop()

    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self._running

    def set_mode(self, mode: SimulationMode) -> None:
        """Set simulation mode."""
        self._mode = mode
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset simulation state."""
        if self._mode == SimulationMode.IDLE:
            self._rpm = 800
            self._speed = 0
            self._gear = 0
            self._throttle = 0
        elif self._mode == SimulationMode.STREET:
            self._rpm = 2000
            self._speed = 50
            self._gear = 3
        elif self._mode == SimulationMode.TRACK_WARMUP:
            self._rpm = 3000
            self._speed = 80
            self._gear = 3
            self._lap_number = 0
            self._lap_time = 0
            self._best_lap = 95.5
        elif self._mode == SimulationMode.TRACK_HOTLAP:
            self._rpm = 6000
            self._speed = 150
            self._gear = 4
            self._lap_number = 3
            self._lap_time = 0
            self._best_lap = 92.345

    def _update(self) -> None:
        """Update simulation."""
        self._time += self._dt

        if self._mode == SimulationMode.IDLE:
            self._simulate_idle()
        elif self._mode == SimulationMode.STREET:
            self._simulate_street()
        elif self._mode == SimulationMode.TRACK_WARMUP:
            self._simulate_track_warmup()
        elif self._mode == SimulationMode.TRACK_HOTLAP:
            self._simulate_track_hotlap()
        elif self._mode == SimulationMode.DRAG_LAUNCH:
            self._simulate_drag()

        self._emit_values()

    def _simulate_idle(self) -> None:
        """Simulate idle engine."""
        # Slight RPM fluctuation
        self._rpm = 800 + 50 * math.sin(self._time * 2) + random.gauss(0, 10)
        self._speed = 0
        self._gear = 0
        self._throttle = 0

        # Update channel values
        self._channel_values[100] = max(0, self._rpm)
        self._channel_values[101] = 0
        self._channel_values[102] = 0
        self._channel_values[110] = 0

    def _simulate_street(self) -> None:
        """Simulate street driving."""
        # Periodic acceleration/deceleration
        cycle = math.sin(self._time * 0.3)

        if cycle > 0.5:
            # Accelerating
            self._throttle = min(100, self._throttle + 2)
            self._rpm = min(6500, self._rpm + 100)
        elif cycle < -0.5:
            # Braking
            self._throttle = max(0, self._throttle - 5)
            self._rpm = max(1500, self._rpm - 150)
        else:
            # Cruising
            self._throttle = 30 + 10 * math.sin(self._time)
            self._rpm = 2500 + 500 * math.sin(self._time * 0.5)

        # Calculate speed from RPM and gear
        gear_ratios = [0, 3.5, 2.1, 1.4, 1.0, 0.8, 0.65]
        if self._rpm > 6000 and self._gear < 6:
            self._gear = min(6, self._gear + 1)
            self._rpm = 4000
        elif self._rpm < 2000 and self._gear > 1:
            self._gear = max(1, self._gear - 1)
            self._rpm = 4500

        self._speed = self._rpm / (gear_ratios[self._gear] * 100) if self._gear > 0 else 0

        self._channel_values[100] = max(0, self._rpm)
        self._channel_values[101] = max(0, self._speed)
        self._channel_values[102] = max(0, self._throttle)
        self._channel_values[110] = self._gear
        self._channel_values[117] = max(0, -cycle * 50) if cycle < 0 else 0  # Brake

    def _simulate_track_warmup(self) -> None:
        """Simulate track warm-up lap."""
        self._lap_time += self._dt

        # Moderate pace
        base_speed = 100 + 30 * math.sin(self._time * 0.2)
        self._speed = base_speed + random.gauss(0, 5)
        self._rpm = 4000 + 1500 * math.sin(self._time * 0.3) + random.gauss(0, 100)
        self._throttle = 40 + 30 * math.sin(self._time * 0.25)

        # Gear based on speed
        if self._speed > 180:
            self._gear = 6
        elif self._speed > 140:
            self._gear = 5
        elif self._speed > 100:
            self._gear = 4
        elif self._speed > 60:
            self._gear = 3
        else:
            self._gear = 2

        # G-forces
        g_lat = 0.5 * math.sin(self._time * 0.4)
        g_lon = 0.3 * math.cos(self._time * 0.3)

        # Complete lap every ~95 seconds
        if self._lap_time > 95:
            self._lap_number += 1
            self._lap_time = 0

        self._channel_values[100] = max(0, self._rpm)
        self._channel_values[101] = max(0, self._speed)
        self._channel_values[102] = max(0, self._throttle)
        self._channel_values[110] = self._gear
        self._channel_values[123] = g_lat
        self._channel_values[124] = g_lon
        self._channel_values[550] = self._lap_time
        self._channel_values[552] = self._best_lap
        self._channel_values[554] = self._lap_number

    def _simulate_track_hotlap(self) -> None:
        """Simulate track hot lap with realistic driving."""
        self._lap_time += self._dt

        # Simulated track sections
        track_position = (self._time % 90) / 90  # 90 second lap

        # Different sections
        if track_position < 0.1:  # Start straight
            self._throttle = 100
            self._speed = 220 + 20 * track_position * 10
            self._rpm = 8000 + 500 * math.sin(self._time * 10)
            self._gear = 6
            g_lat = random.gauss(0, 0.1)
            g_lon = 0.3
            brake = 0
        elif track_position < 0.15:  # Heavy braking
            self._throttle = 0
            self._speed = max(80, self._speed - 10)
            self._rpm = max(4000, self._rpm - 500)
            self._gear = max(3, self._gear - 1) if self._rpm < 5000 else self._gear
            g_lat = random.gauss(0, 0.2)
            g_lon = -1.5
            brake = 120
        elif track_position < 0.25:  # Corner
            self._throttle = 30 + 40 * (track_position - 0.15) * 10
            self._speed = 80 + 30 * (track_position - 0.15) * 10
            self._rpm = 5000 + 2000 * (track_position - 0.15) * 10
            self._gear = 3
            g_lat = 1.5 * math.sin((track_position - 0.15) * 31.4)
            g_lon = 0.5
            brake = 0
        elif track_position < 0.4:  # Acceleration zone
            self._throttle = 100
            self._speed = min(200, self._speed + 5)
            self._rpm = min(8500, self._rpm + 300)
            if self._rpm > 8000 and self._gear < 5:
                self._gear += 1
                self._rpm = 6000
            g_lat = random.gauss(0, 0.2)
            g_lon = 0.8
            brake = 0
        else:  # Mix of corners and straights
            corner_phase = math.sin((track_position - 0.4) * 20)
            if corner_phase > 0.7:  # Straight
                self._throttle = 100
                self._speed = min(230, self._speed + 3)
                self._rpm = min(8500, self._rpm + 200)
                g_lat = random.gauss(0, 0.1)
                g_lon = 0.5
                brake = 0
            elif corner_phase < -0.7:  # Braking
                self._throttle = 0
                self._speed = max(100, self._speed - 8)
                self._rpm = max(5000, self._rpm - 400)
                g_lat = random.gauss(0, 0.3)
                g_lon = -1.2
                brake = 100
            else:  # Corner
                self._throttle = 50 + 30 * corner_phase
                self._speed = 120 + 30 * corner_phase
                self._rpm = 6000 + 1000 * corner_phase
                g_lat = 1.2 * math.cos(corner_phase * 1.57)
                g_lon = 0.3
                brake = max(0, -corner_phase * 30)

        # Update gear based on speed
        if self._speed > 200:
            self._gear = 6
        elif self._speed > 160:
            self._gear = 5
        elif self._speed > 120:
            self._gear = 4
        elif self._speed > 80:
            self._gear = 3
        else:
            self._gear = 2

        # Delta calculation (simulated)
        delta = -0.5 + math.sin(self._time * 0.1) * 2

        # Complete lap
        if self._lap_time > 90:
            last_lap = 90 + random.gauss(0, 1)
            self._channel_values[551] = last_lap
            if last_lap < self._best_lap:
                self._best_lap = last_lap
            self._lap_number += 1
            self._lap_time = 0

        self._channel_values[100] = max(0, min(9000, self._rpm + random.gauss(0, 50)))
        self._channel_values[101] = max(0, self._speed)
        self._channel_values[102] = max(0, min(100, self._throttle))
        self._channel_values[110] = self._gear
        self._channel_values[117] = brake
        self._channel_values[123] = max(-2, min(2, g_lat))
        self._channel_values[124] = max(-2, min(2, g_lon))
        self._channel_values[550] = self._lap_time
        self._channel_values[552] = self._best_lap
        self._channel_values[553] = delta
        self._channel_values[554] = self._lap_number

    def _simulate_drag(self) -> None:
        """Simulate drag race launch."""
        race_time = self._time % 15  # 15 second cycle

        if race_time < 2:  # Staging
            self._rpm = 3000 + 2000 * (race_time / 2)  # Building revs
            self._speed = 0
            self._gear = 1
            self._throttle = 80
        elif race_time < 12:  # Launch and run
            launch_time = race_time - 2
            # Acceleration curve
            self._speed = 35 * launch_time - 1.5 * launch_time * launch_time + 0.1 * launch_time * launch_time * launch_time
            self._speed = max(0, min(250, self._speed))

            # Gear shifts
            if self._speed > 200:
                self._gear = 6
                self._rpm = 7000
            elif self._speed > 160:
                self._gear = 5
                self._rpm = 7500
            elif self._speed > 120:
                self._gear = 4
                self._rpm = 8000
            elif self._speed > 80:
                self._gear = 3
                self._rpm = 8200
            elif self._speed > 40:
                self._gear = 2
                self._rpm = 8500
            else:
                self._gear = 1
                self._rpm = 8500 - launch_time * 200

            self._throttle = 100
        else:  # Slow down
            self._throttle = 0
            self._speed = max(0, self._speed - 15)
            self._rpm = max(1000, self._rpm - 500)

        self._channel_values[100] = max(0, self._rpm)
        self._channel_values[101] = max(0, self._speed)
        self._channel_values[102] = self._throttle
        self._channel_values[110] = self._gear
        self._channel_values[124] = 1.5 if race_time > 2 and race_time < 5 else 0  # Launch G

    def _emit_values(self) -> None:
        """Emit current values."""
        # Add background simulation for other channels
        for ch_id, config in self._channel_configs.items():
            if ch_id not in self._channel_values:
                # Generate value from config
                value = config.base_value
                if config.amplitude > 0:
                    value += config.amplitude * math.sin(self._time * config.frequency * 2 * math.pi)
                if config.noise > 0:
                    value += random.gauss(0, config.noise)
                value = max(config.min_value, min(config.max_value, value))
                self._channel_values[ch_id] = value

        self.data_updated.emit(self._channel_values.copy())

    def get_value(self, channel_id: int) -> float:
        """Get current value for channel."""
        return self._channel_values.get(channel_id, 0.0)

    def set_update_rate(self, hz: int) -> None:
        """Set update rate in Hz."""
        self._dt = 1.0 / hz
        if self._running:
            self._timer.setInterval(int(self._dt * 1000))
