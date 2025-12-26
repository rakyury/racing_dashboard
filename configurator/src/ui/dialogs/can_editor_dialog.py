# CAN Message Editor Dialog
"""Dialog for editing CAN messages and signals, importing DBC files."""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem,
    QFormLayout, QWidget, QFrame, QMenu, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from models.can_database import (
    CANDatabase, CANMessage, CANSignal,
    ByteOrder, ValueType, DBCParser
)
from models.ecu_presets import (
    ECUPreset, ECUBrand, get_all_presets, get_presets_by_brand
)
from models.channel_types import get_all_predefined_channels, get_channel_by_id


class SignalEditorWidget(QWidget):
    """Widget for editing a single CAN signal."""

    signal_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._signal: Optional[CANSignal] = None
        self._updating = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(8)

        # Name
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_changed)
        layout.addRow("Name:", self._name_edit)

        # Start bit
        self._start_bit = QSpinBox()
        self._start_bit.setRange(0, 63)
        self._start_bit.valueChanged.connect(self._on_changed)
        layout.addRow("Start Bit:", self._start_bit)

        # Bit length
        self._bit_length = QSpinBox()
        self._bit_length.setRange(1, 64)
        self._bit_length.setValue(8)
        self._bit_length.valueChanged.connect(self._on_changed)
        layout.addRow("Bit Length:", self._bit_length)

        # Byte order
        self._byte_order = QComboBox()
        self._byte_order.addItems(["Big Endian (Motorola)", "Little Endian (Intel)"])
        self._byte_order.currentIndexChanged.connect(self._on_changed)
        layout.addRow("Byte Order:", self._byte_order)

        # Value type
        self._value_type = QComboBox()
        self._value_type.addItems(["Unsigned", "Signed"])
        self._value_type.currentIndexChanged.connect(self._on_changed)
        layout.addRow("Value Type:", self._value_type)

        # Scale
        self._scale = QDoubleSpinBox()
        self._scale.setRange(0.0001, 1000000)
        self._scale.setDecimals(6)
        self._scale.setValue(1.0)
        self._scale.valueChanged.connect(self._on_changed)
        layout.addRow("Scale:", self._scale)

        # Offset
        self._offset = QDoubleSpinBox()
        self._offset.setRange(-1000000, 1000000)
        self._offset.setDecimals(4)
        self._offset.setValue(0.0)
        self._offset.valueChanged.connect(self._on_changed)
        layout.addRow("Offset:", self._offset)

        # Min/Max
        min_max_layout = QHBoxLayout()
        self._min_value = QDoubleSpinBox()
        self._min_value.setRange(-1000000, 1000000)
        self._min_value.valueChanged.connect(self._on_changed)
        min_max_layout.addWidget(QLabel("Min:"))
        min_max_layout.addWidget(self._min_value)

        self._max_value = QDoubleSpinBox()
        self._max_value.setRange(-1000000, 1000000)
        self._max_value.setValue(100)
        self._max_value.valueChanged.connect(self._on_changed)
        min_max_layout.addWidget(QLabel("Max:"))
        min_max_layout.addWidget(self._max_value)
        layout.addRow("Range:", min_max_layout)

        # Unit
        self._unit = QLineEdit()
        self._unit.setMaxLength(16)
        self._unit.textChanged.connect(self._on_changed)
        layout.addRow("Unit:", self._unit)

        # Channel mapping
        self._channel_combo = QComboBox()
        self._channel_combo.addItem("(None)", 0)
        for channel in get_all_predefined_channels():
            display = f"{channel.name} [{channel.units}]" if channel.units else channel.name
            self._channel_combo.addItem(display, channel.id)
        self._channel_combo.currentIndexChanged.connect(self._on_changed)
        layout.addRow("Map to Channel:", self._channel_combo)

        self.setEnabled(False)

    def set_signal(self, signal: Optional[CANSignal]) -> None:
        """Set signal to edit."""
        self._signal = signal
        self.setEnabled(signal is not None)

        if signal:
            self._updating = True
            self._name_edit.setText(signal.name)
            self._start_bit.setValue(signal.start_bit)
            self._bit_length.setValue(signal.bit_length)
            self._byte_order.setCurrentIndex(0 if signal.byte_order == ByteOrder.BIG_ENDIAN else 1)
            self._value_type.setCurrentIndex(0 if signal.value_type == ValueType.UNSIGNED else 1)
            self._scale.setValue(signal.scale)
            self._offset.setValue(signal.offset)
            self._min_value.setValue(signal.min_value)
            self._max_value.setValue(signal.max_value)
            self._unit.setText(signal.unit)

            # Find channel in combo
            idx = self._channel_combo.findData(signal.channel_id or 0)
            if idx >= 0:
                self._channel_combo.setCurrentIndex(idx)

            self._updating = False

    def _on_changed(self) -> None:
        """Handle value changed."""
        if self._updating or not self._signal:
            return

        self._signal.name = self._name_edit.text()
        self._signal.start_bit = self._start_bit.value()
        self._signal.bit_length = self._bit_length.value()
        self._signal.byte_order = ByteOrder.BIG_ENDIAN if self._byte_order.currentIndex() == 0 else ByteOrder.LITTLE_ENDIAN
        self._signal.value_type = ValueType.UNSIGNED if self._value_type.currentIndex() == 0 else ValueType.SIGNED
        self._signal.scale = self._scale.value()
        self._signal.offset = self._offset.value()
        self._signal.min_value = self._min_value.value()
        self._signal.max_value = self._max_value.value()
        self._signal.unit = self._unit.text()
        self._signal.channel_id = self._channel_combo.currentData()

        self.signal_changed.emit()


class CANEditorDialog(QDialog):
    """Dialog for editing CAN database."""

    database_changed = pyqtSignal(object)  # CANDatabase

    def __init__(self, database: Optional[CANDatabase] = None, parent=None):
        super().__init__(parent)
        self._database = database or CANDatabase()
        self._current_message: Optional[CANMessage] = None
        self._current_signal: Optional[CANSignal] = None

        self.setWindowTitle("CAN Message Editor")
        self.setMinimumSize(900, 600)
        self._setup_style()
        self._setup_ui()
        self._populate_tree()

    def _setup_style(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
            }
            QLabel {
                color: #ddd;
            }
            QGroupBox {
                color: #aaa;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
            QTreeWidget, QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                color: #ddd;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #ddd;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ddd;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QPushButton#primaryBtn {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()

        import_btn = QPushButton("Import DBC...")
        import_btn.clicked.connect(self._import_dbc)
        toolbar.addWidget(import_btn)

        export_btn = QPushButton("Export DBC...")
        export_btn.clicked.connect(self._export_dbc)
        toolbar.addWidget(export_btn)

        toolbar.addWidget(QLabel("  |  "))

        preset_btn = QPushButton("Load ECU Preset...")
        preset_btn.clicked.connect(self._show_preset_menu)
        toolbar.addWidget(preset_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - message tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        msg_label = QLabel("Messages")
        msg_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(msg_label)

        self._msg_tree = QTreeWidget()
        self._msg_tree.setHeaderLabels(["Name", "ID"])
        self._msg_tree.setColumnWidth(0, 150)
        self._msg_tree.itemClicked.connect(self._on_tree_item_clicked)
        self._msg_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._msg_tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        left_layout.addWidget(self._msg_tree)

        # Add/Remove message buttons
        msg_btn_layout = QHBoxLayout()
        add_msg_btn = QPushButton("+ Message")
        add_msg_btn.clicked.connect(self._add_message)
        msg_btn_layout.addWidget(add_msg_btn)

        remove_msg_btn = QPushButton("- Remove")
        remove_msg_btn.clicked.connect(self._remove_selected)
        msg_btn_layout.addWidget(remove_msg_btn)
        left_layout.addLayout(msg_btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Message properties
        msg_group = QGroupBox("Message Properties")
        msg_form = QFormLayout(msg_group)

        self._msg_name = QLineEdit()
        self._msg_name.textChanged.connect(self._on_message_changed)
        msg_form.addRow("Name:", self._msg_name)

        id_layout = QHBoxLayout()
        self._msg_id = QSpinBox()
        self._msg_id.setRange(0, 0x1FFFFFFF)
        self._msg_id.setDisplayIntegerBase(16)
        self._msg_id.setPrefix("0x")
        self._msg_id.valueChanged.connect(self._on_message_changed)
        id_layout.addWidget(self._msg_id)

        self._msg_extended = QCheckBox("Extended ID")
        self._msg_extended.stateChanged.connect(self._on_message_changed)
        id_layout.addWidget(self._msg_extended)
        msg_form.addRow("ID:", id_layout)

        self._msg_dlc = QSpinBox()
        self._msg_dlc.setRange(0, 64)
        self._msg_dlc.setValue(8)
        self._msg_dlc.valueChanged.connect(self._on_message_changed)
        msg_form.addRow("DLC:", self._msg_dlc)

        self._msg_cycle = QSpinBox()
        self._msg_cycle.setRange(0, 10000)
        self._msg_cycle.setSuffix(" ms")
        self._msg_cycle.valueChanged.connect(self._on_message_changed)
        msg_form.addRow("Cycle Time:", self._msg_cycle)

        right_layout.addWidget(msg_group)

        # Signals table
        sig_group = QGroupBox("Signals")
        sig_layout = QVBoxLayout(sig_group)

        self._signal_table = QTableWidget()
        self._signal_table.setColumnCount(6)
        self._signal_table.setHorizontalHeaderLabels(["Name", "Start", "Length", "Scale", "Unit", "Channel"])
        self._signal_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._signal_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._signal_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._signal_table.itemSelectionChanged.connect(self._on_signal_selected)
        sig_layout.addWidget(self._signal_table)

        # Signal buttons
        sig_btn_layout = QHBoxLayout()
        add_sig_btn = QPushButton("+ Signal")
        add_sig_btn.clicked.connect(self._add_signal)
        sig_btn_layout.addWidget(add_sig_btn)

        remove_sig_btn = QPushButton("- Remove")
        remove_sig_btn.clicked.connect(self._remove_signal)
        sig_btn_layout.addWidget(remove_sig_btn)
        sig_btn_layout.addStretch()
        sig_layout.addLayout(sig_btn_layout)

        right_layout.addWidget(sig_group)

        # Signal editor
        sig_edit_group = QGroupBox("Signal Properties")
        self._signal_editor = SignalEditorWidget()
        self._signal_editor.signal_changed.connect(self._refresh_signal_table)
        sig_edit_layout = QVBoxLayout(sig_edit_group)
        sig_edit_layout.addWidget(self._signal_editor)
        right_layout.addWidget(sig_edit_group)

        splitter.addWidget(right_panel)
        splitter.setSizes([250, 650])
        layout.addWidget(splitter)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

        self._set_message_enabled(False)

    def _populate_tree(self) -> None:
        """Populate message tree."""
        self._msg_tree.clear()

        for msg in self._database.messages:
            item = QTreeWidgetItem()
            item.setText(0, msg.name)
            item.setText(1, f"0x{msg.id:X}")
            item.setData(0, Qt.ItemDataRole.UserRole, msg)
            self._msg_tree.addTopLevelItem(item)

            for sig in msg.signals:
                sig_item = QTreeWidgetItem(item)
                sig_item.setText(0, sig.name)
                sig_item.setText(1, sig.unit)
                sig_item.setData(0, Qt.ItemDataRole.UserRole, sig)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle tree item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(data, CANMessage):
            self._select_message(data)
        elif isinstance(data, CANSignal):
            # Select parent message first
            parent = item.parent()
            if parent:
                msg = parent.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(msg, CANMessage):
                    self._select_message(msg)
            self._signal_editor.set_signal(data)
            self._current_signal = data

    def _select_message(self, msg: CANMessage) -> None:
        """Select a message for editing."""
        self._current_message = msg
        self._set_message_enabled(True)

        # Update message fields
        self._msg_name.blockSignals(True)
        self._msg_id.blockSignals(True)
        self._msg_extended.blockSignals(True)
        self._msg_dlc.blockSignals(True)
        self._msg_cycle.blockSignals(True)

        self._msg_name.setText(msg.name)
        self._msg_id.setValue(msg.id)
        self._msg_extended.setChecked(msg.extended)
        self._msg_dlc.setValue(msg.dlc)
        self._msg_cycle.setValue(msg.cycle_time_ms)

        self._msg_name.blockSignals(False)
        self._msg_id.blockSignals(False)
        self._msg_extended.blockSignals(False)
        self._msg_dlc.blockSignals(False)
        self._msg_cycle.blockSignals(False)

        self._refresh_signal_table()

    def _set_message_enabled(self, enabled: bool) -> None:
        """Enable/disable message editing."""
        self._msg_name.setEnabled(enabled)
        self._msg_id.setEnabled(enabled)
        self._msg_extended.setEnabled(enabled)
        self._msg_dlc.setEnabled(enabled)
        self._msg_cycle.setEnabled(enabled)
        self._signal_table.setEnabled(enabled)

    def _refresh_signal_table(self) -> None:
        """Refresh signal table."""
        self._signal_table.setRowCount(0)

        if not self._current_message:
            return

        for sig in self._current_message.signals:
            row = self._signal_table.rowCount()
            self._signal_table.insertRow(row)

            self._signal_table.setItem(row, 0, QTableWidgetItem(sig.name))
            self._signal_table.setItem(row, 1, QTableWidgetItem(str(sig.start_bit)))
            self._signal_table.setItem(row, 2, QTableWidgetItem(str(sig.bit_length)))
            self._signal_table.setItem(row, 3, QTableWidgetItem(f"{sig.scale}"))
            self._signal_table.setItem(row, 4, QTableWidgetItem(sig.unit))

            channel_text = ""
            if sig.channel_id:
                ch = get_channel_by_id(sig.channel_id)
                if ch:
                    channel_text = ch.name
            self._signal_table.setItem(row, 5, QTableWidgetItem(channel_text))

        self._populate_tree()

    def _on_message_changed(self) -> None:
        """Handle message property change."""
        if not self._current_message:
            return

        self._current_message.name = self._msg_name.text()
        self._current_message.id = self._msg_id.value()
        self._current_message.extended = self._msg_extended.isChecked()
        self._current_message.dlc = self._msg_dlc.value()
        self._current_message.cycle_time_ms = self._msg_cycle.value()

        self._populate_tree()

    def _on_signal_selected(self) -> None:
        """Handle signal selection in table."""
        rows = self._signal_table.selectionModel().selectedRows()
        if rows and self._current_message:
            row = rows[0].row()
            if 0 <= row < len(self._current_message.signals):
                sig = self._current_message.signals[row]
                self._signal_editor.set_signal(sig)
                self._current_signal = sig

    def _add_message(self) -> None:
        """Add new message."""
        # Find unique ID
        used_ids = {m.id for m in self._database.messages}
        new_id = 0x100
        while new_id in used_ids:
            new_id += 1

        msg = CANMessage(
            id=new_id,
            name=f"Message_{new_id:X}",
            dlc=8
        )
        self._database.add_message(msg)
        self._populate_tree()
        self._select_message(msg)

    def _add_signal(self) -> None:
        """Add signal to current message."""
        if not self._current_message:
            return

        # Find next available start bit
        used_bits = set()
        for sig in self._current_message.signals:
            for b in range(sig.start_bit, sig.start_bit + sig.bit_length):
                used_bits.add(b)

        start_bit = 0
        while start_bit in used_bits:
            start_bit += 8

        sig = CANSignal(
            name=f"Signal_{len(self._current_message.signals) + 1}",
            start_bit=start_bit,
            bit_length=8
        )
        self._current_message.add_signal(sig)
        self._refresh_signal_table()
        self._signal_editor.set_signal(sig)

    def _remove_selected(self) -> None:
        """Remove selected message or signal."""
        item = self._msg_tree.currentItem()
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, CANMessage):
            self._database.remove_message(data.id)
            self._current_message = None
            self._set_message_enabled(False)
        elif isinstance(data, CANSignal) and self._current_message:
            self._current_message.remove_signal(data.name)
            self._signal_editor.set_signal(None)

        self._populate_tree()
        self._refresh_signal_table()

    def _remove_signal(self) -> None:
        """Remove selected signal."""
        if not self._current_message or not self._current_signal:
            return

        self._current_message.remove_signal(self._current_signal.name)
        self._current_signal = None
        self._signal_editor.set_signal(None)
        self._refresh_signal_table()

    def _show_tree_context_menu(self, pos) -> None:
        """Show context menu for tree."""
        menu = QMenu(self)
        menu.addAction("Add Message", self._add_message)

        item = self._msg_tree.itemAt(pos)
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, CANMessage):
                menu.addAction("Add Signal", self._add_signal)
            menu.addSeparator()
            menu.addAction("Remove", self._remove_selected)

        menu.exec(self._msg_tree.mapToGlobal(pos))

    def _import_dbc(self) -> None:
        """Import DBC file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import DBC File",
            "", "DBC Files (*.dbc);;All Files (*)"
        )

        if file_path:
            try:
                self._database = DBCParser.parse_file(file_path)
                self._populate_tree()
                self._current_message = None
                self._set_message_enabled(False)
                QMessageBox.information(
                    self, "Import Complete",
                    f"Imported {len(self._database.messages)} messages"
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import DBC:\n{e}")

    def _export_dbc(self) -> None:
        """Export to DBC file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export DBC File",
            "", "DBC Files (*.dbc);;All Files (*)"
        )

        if file_path:
            if not file_path.endswith('.dbc'):
                file_path += '.dbc'
            try:
                DBCParser.export_file(self._database, file_path)
                QMessageBox.information(self, "Export Complete", "DBC file exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export DBC:\n{e}")

    def _show_preset_menu(self) -> None:
        """Show ECU preset selection menu."""
        menu = QMenu(self)

        presets_by_brand = get_presets_by_brand()
        for brand, presets in presets_by_brand.items():
            submenu = menu.addMenu(brand.value)
            for preset in presets:
                action = submenu.addAction(preset.model)
                action.setData(preset)
                action.triggered.connect(lambda checked, p=preset: self._load_preset(p))

        menu.exec(self.cursor().pos())

    def _load_preset(self, preset: ECUPreset) -> None:
        """Load ECU preset."""
        reply = QMessageBox.question(
            self, "Load Preset",
            f"Load {preset.brand.value} {preset.model} preset?\n\n"
            "This will replace the current database.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._database = CANDatabase(
                name=preset.database.name,
                version=preset.database.version
            )
            # Deep copy messages
            for msg in preset.database.messages:
                new_msg = CANMessage.from_dict(msg.to_dict())
                self._database.add_message(new_msg)

            self._populate_tree()
            self._current_message = None
            self._set_message_enabled(False)

    def _on_ok(self) -> None:
        """Handle OK button."""
        self.database_changed.emit(self._database)
        self.accept()

    def get_database(self) -> CANDatabase:
        """Get the edited database."""
        return self._database


def show_can_editor(database: Optional[CANDatabase] = None, parent=None) -> Optional[CANDatabase]:
    """Show CAN editor dialog."""
    dialog = CANEditorDialog(database, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_database()
    return None
