# Monitor Panel Widget
"""Live monitoring widgets for CAN, telemetry, GPS, and logs."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton, QFrame,
    QSplitter, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QGroupBox, QGridLayout, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush

logger = logging.getLogger(__name__)


class CANMonitorWidget(QWidget):
    """Real-time CAN bus message monitor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: Dict[int, Dict] = {}  # CAN ID -> last message
        self._message_history: deque = deque(maxlen=1000)
        self._paused = False
        self._filter_id: Optional[int] = None

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        toolbar = QHBoxLayout()

        self._pause_btn = QPushButton("⏸ Pause")
        self._pause_btn.setCheckable(True)
        self._pause_btn.toggled.connect(self._toggle_pause)
        toolbar.addWidget(self._pause_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_messages)
        toolbar.addWidget(self._clear_btn)

        toolbar.addWidget(QLabel("Filter ID:"))
        self._filter_input = QComboBox()
        self._filter_input.setEditable(True)
        self._filter_input.addItem("All")
        self._filter_input.setMinimumWidth(100)
        self._filter_input.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._filter_input)

        self._hex_check = QCheckBox("Hex Data")
        self._hex_check.setChecked(True)
        toolbar.addWidget(self._hex_check)

        toolbar.addStretch()

        self._msg_count_label = QLabel("0 messages")
        toolbar.addWidget(self._msg_count_label)

        layout.addLayout(toolbar)

        # Message table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Time", "ID", "DLC", "Data", "Count", "Δt (ms)"
        ])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(1, 70)
        self._table.setColumnWidth(2, 40)
        self._table.setColumnWidth(4, 60)
        self._table.setColumnWidth(5, 70)

        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

        # Stats bar
        stats = QHBoxLayout()
        self._bus_load_label = QLabel("Bus Load: 0%")
        stats.addWidget(self._bus_load_label)
        self._rate_label = QLabel("Rate: 0 msg/s")
        stats.addWidget(self._rate_label)
        stats.addStretch()
        layout.addLayout(stats)

    def _setup_timer(self) -> None:
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(100)  # 10 Hz update

    def _toggle_pause(self, paused: bool) -> None:
        self._paused = paused
        self._pause_btn.setText("▶ Resume" if paused else "⏸ Pause")

    def _clear_messages(self) -> None:
        self._messages.clear()
        self._message_history.clear()
        self._table.setRowCount(0)
        self._msg_count_label.setText("0 messages")

    def _on_filter_changed(self, text: str) -> None:
        if text == "All" or text == "":
            self._filter_id = None
        else:
            try:
                self._filter_id = int(text, 16) if text.startswith("0x") else int(text)
            except ValueError:
                self._filter_id = None

    def add_message(self, can_id: int, data: bytes, timestamp: float = None) -> None:
        """Add a CAN message to the monitor."""
        if self._paused:
            return

        if timestamp is None:
            timestamp = datetime.now().timestamp()

        # Update message store
        if can_id in self._messages:
            prev = self._messages[can_id]
            delta_t = (timestamp - prev["timestamp"]) * 1000
            count = prev["count"] + 1
        else:
            delta_t = 0
            count = 1

        self._messages[can_id] = {
            "data": data,
            "timestamp": timestamp,
            "count": count,
            "delta_t": delta_t,
        }

        # Add to history
        self._message_history.append({
            "id": can_id,
            "data": data,
            "timestamp": timestamp,
        })

        # Update filter dropdown if new ID
        id_str = f"0x{can_id:03X}"
        if self._filter_input.findText(id_str) == -1:
            self._filter_input.addItem(id_str)

    def _update_display(self) -> None:
        """Update the display table."""
        if self._paused:
            return

        # Get filtered messages
        messages = []
        for can_id, msg in sorted(self._messages.items()):
            if self._filter_id is None or can_id == self._filter_id:
                messages.append((can_id, msg))

        # Update table
        self._table.setRowCount(len(messages))

        for row, (can_id, msg) in enumerate(messages):
            # Time
            time_str = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S.%f")[:-3]
            self._table.setItem(row, 0, QTableWidgetItem(time_str))

            # ID
            id_item = QTableWidgetItem(f"0x{can_id:03X}")
            id_item.setForeground(QColor("#4FC3F7"))
            self._table.setItem(row, 1, id_item)

            # DLC
            self._table.setItem(row, 2, QTableWidgetItem(str(len(msg["data"]))))

            # Data
            if self._hex_check.isChecked():
                data_str = " ".join(f"{b:02X}" for b in msg["data"])
            else:
                data_str = " ".join(f"{b:3d}" for b in msg["data"])
            data_item = QTableWidgetItem(data_str)
            data_item.setFont(QFont("Consolas", 9))
            self._table.setItem(row, 3, data_item)

            # Count
            self._table.setItem(row, 4, QTableWidgetItem(str(msg["count"])))

            # Delta time
            delta_item = QTableWidgetItem(f"{msg['delta_t']:.1f}")
            self._table.setItem(row, 5, delta_item)

        self._msg_count_label.setText(f"{len(self._messages)} IDs | {len(self._message_history)} total")


class TelemetryWidget(QWidget):
    """Telemetry data display with gauges and values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: Dict[str, float] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Status
        status_layout = QHBoxLayout()
        self._status_label = QLabel("⚪ Not Connected")
        self._status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        self._connect_btn = QPushButton("Connect Emulator")
        status_layout.addWidget(self._connect_btn)
        layout.addLayout(status_layout)

        # Scroll area for telemetry items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._grid = QGridLayout(content)
        self._grid.setSpacing(8)

        # Create telemetry display items
        self._items: Dict[str, TelemetryItem] = {}
        telemetry_channels = [
            ("RPM", "rpm", 0, 9000, ""),
            ("Speed", "km/h", 0, 300, "speed"),
            ("Gear", "", 0, 6, "gear"),
            ("Throttle", "%", 0, 100, "throttle"),
            ("Brake", "%", 0, 100, "brake"),
            ("Coolant", "°C", 0, 130, "coolant_temp"),
            ("Oil Temp", "°C", 0, 150, "oil_temp"),
            ("Oil Press", "bar", 0, 8, "oil_pressure"),
            ("Fuel", "%", 0, 100, "fuel_level"),
            ("Battery", "V", 10, 15, "battery"),
            ("G Lat", "g", -2, 2, "g_lat"),
            ("G Lon", "g", -2, 2, "g_lon"),
        ]

        for i, (name, unit, min_val, max_val, key) in enumerate(telemetry_channels):
            item = TelemetryItem(name, unit, min_val, max_val)
            self._items[key or name.lower()] = item
            row = i // 4
            col = i % 4
            self._grid.addWidget(item, row, col)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def set_connected(self, connected: bool) -> None:
        if connected:
            self._status_label.setText("🟢 Connected")
            self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self._status_label.setText("⚪ Not Connected")
            self._status_label.setStyleSheet("font-weight: bold;")

    def update_values(self, data: Dict[str, float]) -> None:
        """Update telemetry values."""
        for key, value in data.items():
            if key in self._items:
                self._items[key].set_value(value)


class TelemetryItem(QFrame):
    """Single telemetry display item."""

    def __init__(self, name: str, unit: str, min_val: float, max_val: float, parent=None):
        super().__init__(parent)
        self._name = name
        self._unit = unit
        self._min = min_val
        self._max = max_val
        self._value = 0.0

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            TelemetryItem {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        self.setMinimumSize(120, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet("color: #888; font-size: 10px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setMaximumHeight(8)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("""
            QProgressBar {
                background-color: #333;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._bar)

    def set_value(self, value: float) -> None:
        self._value = value

        # Format value
        if abs(value) >= 1000:
            text = f"{value:.0f}"
        elif abs(value) >= 100:
            text = f"{value:.1f}"
        else:
            text = f"{value:.2f}"

        if self._unit:
            text += f" {self._unit}"

        self._value_label.setText(text)

        # Update progress bar
        if self._max > self._min:
            percent = int(100 * (value - self._min) / (self._max - self._min))
            self._bar.setValue(max(0, min(100, percent)))


class GPSWidget(QWidget):
    """GPS data display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # GPS Status
        status_group = QGroupBox("GPS Status")
        status_layout = QGridLayout(status_group)

        self._fix_label = QLabel("No Fix")
        status_layout.addWidget(QLabel("Fix:"), 0, 0)
        status_layout.addWidget(self._fix_label, 0, 1)

        self._sats_label = QLabel("0")
        status_layout.addWidget(QLabel("Satellites:"), 1, 0)
        status_layout.addWidget(self._sats_label, 1, 1)

        self._hdop_label = QLabel("--")
        status_layout.addWidget(QLabel("HDOP:"), 2, 0)
        status_layout.addWidget(self._hdop_label, 2, 1)

        layout.addWidget(status_group)

        # Position
        pos_group = QGroupBox("Position")
        pos_layout = QGridLayout(pos_group)

        self._lat_label = QLabel("--")
        pos_layout.addWidget(QLabel("Latitude:"), 0, 0)
        pos_layout.addWidget(self._lat_label, 0, 1)

        self._lon_label = QLabel("--")
        pos_layout.addWidget(QLabel("Longitude:"), 1, 0)
        pos_layout.addWidget(self._lon_label, 1, 1)

        self._alt_label = QLabel("--")
        pos_layout.addWidget(QLabel("Altitude:"), 2, 0)
        pos_layout.addWidget(self._alt_label, 2, 1)

        self._speed_label = QLabel("--")
        pos_layout.addWidget(QLabel("Speed:"), 3, 0)
        pos_layout.addWidget(self._speed_label, 3, 1)

        self._heading_label = QLabel("--")
        pos_layout.addWidget(QLabel("Heading:"), 4, 0)
        pos_layout.addWidget(self._heading_label, 4, 1)

        layout.addWidget(pos_group)

        # Track
        track_group = QGroupBox("Track Detection")
        track_layout = QVBoxLayout(track_group)

        self._track_label = QLabel("No track detected")
        track_layout.addWidget(self._track_label)

        layout.addWidget(track_group)
        layout.addStretch()

    def update_gps(self, data: Dict[str, Any]) -> None:
        """Update GPS display."""
        if "fix" in data:
            fix_types = {0: "No Fix", 1: "2D Fix", 2: "3D Fix", 3: "DGPS"}
            self._fix_label.setText(fix_types.get(data["fix"], "Unknown"))

        if "satellites" in data:
            self._sats_label.setText(str(data["satellites"]))

        if "hdop" in data:
            self._hdop_label.setText(f"{data['hdop']:.1f}")

        if "latitude" in data:
            self._lat_label.setText(f"{data['latitude']:.6f}°")

        if "longitude" in data:
            self._lon_label.setText(f"{data['longitude']:.6f}°")

        if "altitude" in data:
            self._alt_label.setText(f"{data['altitude']:.1f} m")

        if "speed" in data:
            self._speed_label.setText(f"{data['speed']:.1f} km/h")

        if "heading" in data:
            self._heading_label.setText(f"{data['heading']:.1f}°")

        if "track" in data:
            self._track_label.setText(data["track"])


class LogWidget(QWidget):
    """Device log viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        toolbar = QHBoxLayout()

        self._level_combo = QComboBox()
        self._level_combo.addItems(["All", "Debug", "Info", "Warning", "Error"])
        toolbar.addWidget(QLabel("Level:"))
        toolbar.addWidget(self._level_combo)

        self._autoscroll_check = QCheckBox("Auto-scroll")
        self._autoscroll_check.setChecked(True)
        toolbar.addWidget(self._autoscroll_check)

        toolbar.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_log)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Log text
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 9))
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ddd;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self._log_text)

    def _clear_log(self) -> None:
        self._log_text.clear()

    def add_log(self, level: str, message: str, timestamp: float = None) -> None:
        """Add a log entry."""
        if timestamp is None:
            time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        else:
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]

        colors = {
            "debug": "#888",
            "info": "#4FC3F7",
            "warning": "#FFB74D",
            "error": "#EF5350",
        }
        color = colors.get(level.lower(), "#ddd")

        html = f'<span style="color:#666">[{time_str}]</span> '
        html += f'<span style="color:{color}">[{level.upper()}]</span> '
        html += f'<span style="color:#ddd">{message}</span><br>'

        self._log_text.insertHtml(html)

        if self._autoscroll_check.isChecked():
            self._log_text.verticalScrollBar().setValue(
                self._log_text.verticalScrollBar().maximum()
            )


class MonitorPanel(QTabWidget):
    """Complete monitor panel with all monitoring tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create tabs
        self._can_monitor = CANMonitorWidget()
        self.addTab(self._can_monitor, "CAN Bus")

        self._telemetry = TelemetryWidget()
        self.addTab(self._telemetry, "Telemetry")

        self._gps = GPSWidget()
        self.addTab(self._gps, "GPS")

        self._logs = LogWidget()
        self.addTab(self._logs, "Logs")

    @property
    def can_monitor(self) -> CANMonitorWidget:
        return self._can_monitor

    @property
    def telemetry(self) -> TelemetryWidget:
        return self._telemetry

    @property
    def gps(self) -> GPSWidget:
        return self._gps

    @property
    def logs(self) -> LogWidget:
        return self._logs

    def set_connected(self, connected: bool) -> None:
        """Update connection state."""
        self._telemetry.set_connected(connected)

    def add_can_message(self, can_id: int, data: bytes) -> None:
        """Add CAN message to monitor."""
        self._can_monitor.add_message(can_id, data)

    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update telemetry values."""
        self._telemetry.update_values(data)

    def update_gps(self, data: Dict[str, Any]) -> None:
        """Update GPS data."""
        self._gps.update_gps(data)

    def add_log(self, level: str, message: str) -> None:
        """Add log entry."""
        self._logs.add_log(level, message)
