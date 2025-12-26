# Main Window
"""Main application window with dock-based layout."""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QFrame, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from utils.constants import (
    APP_NAME, APP_VERSION, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    DOCK_MIN_WIDTH, CONFIG_EXTENSION
)
from utils.theme import ThemeManager
from models.config_manager import ConfigManager
from controllers.device_controller import DeviceController
from ui.screen_editor.screen_editor_widget import ScreenEditorWidget
from ui.dialogs import DialogFactory, has_dialog, show_template_dialog
from ui.dialogs.can_editor_dialog import show_can_editor
from ui.dialogs.firmware_dialog import show_firmware_dialog
from ui.widgets.monitor_panel import MonitorPanel
from models.config_exporter import ConfigExporter, export_for_device

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    Uses dock widgets for flexible layout similar to PMU_30.
    """

    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._config_manager = ConfigManager()
        self._device_controller = DeviceController(self)
        self._settings = QSettings()

        self._setup_window()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_status_bar()
        self._create_dock_widgets()
        self._create_central_widget()
        self._connect_signals()
        self._restore_state()
        self._update_title()

        # Create new configuration on startup
        self._config_manager.new_configuration()
        self._sync_screens_to_editor()

        # Create dialog factory
        self._dialog_factory = DialogFactory(self._config_manager.config, self)

    def _setup_window(self) -> None:
        """Setup main window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setDockNestingEnabled(True)

    def _create_actions(self) -> None:
        """Create menu and toolbar actions."""
        # File actions
        self.action_new = QAction("&New", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self.new_configuration)

        self.action_open = QAction("&Open...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.open_configuration)

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.save_configuration)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_as.triggered.connect(self.save_configuration_as)

        self.action_export_json = QAction("Export for &Device (JSON)...", self)
        self.action_export_json.setShortcut(QKeySequence("Ctrl+E"))
        self.action_export_json.triggered.connect(self.export_for_device_json)

        self.action_export_binary = QAction("Export &Binary...", self)
        self.action_export_binary.triggered.connect(self.export_for_device_binary)

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.triggered.connect(self.close)

        # Edit actions
        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.setEnabled(False)

        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.setEnabled(False)

        # Device actions
        self.action_connect = QAction("&Connect...", self)
        self.action_connect.triggered.connect(self.show_connect_dialog)

        self.action_disconnect = QAction("&Disconnect", self)
        self.action_disconnect.setEnabled(False)
        self.action_disconnect.triggered.connect(self.disconnect_device)

        self.action_read_config = QAction("&Read from Device", self)
        self.action_read_config.setEnabled(False)
        self.action_read_config.triggered.connect(self.read_from_device)

        self.action_write_config = QAction("&Write to Device", self)
        self.action_write_config.setEnabled(False)
        self.action_write_config.triggered.connect(self.write_to_device)

        self.action_connect_emulator = QAction("Connect &Emulator", self)
        self.action_connect_emulator.triggered.connect(self.connect_emulator)

        self.action_firmware_upload = QAction("&Firmware Upload...", self)
        self.action_firmware_upload.triggered.connect(self.show_firmware_dialog)

        # View actions
        self.action_toggle_theme = QAction("Toggle &Theme", self)
        self.action_toggle_theme.triggered.connect(self.toggle_theme)

        # Tools actions
        self.action_can_editor = QAction("&CAN Message Editor...", self)
        self.action_can_editor.triggered.connect(self.show_can_editor)

        # Help actions
        self.action_about = QAction("&About", self)
        self.action_about.triggered.connect(self.show_about)

    def _create_menus(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        export_menu.addAction(self.action_export_json)
        export_menu.addAction(self.action_export_binary)

        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)

        # Device menu
        device_menu = menubar.addMenu("&Device")
        device_menu.addAction(self.action_connect)
        device_menu.addAction(self.action_disconnect)
        device_menu.addSeparator()
        device_menu.addAction(self.action_read_config)
        device_menu.addAction(self.action_write_config)
        device_menu.addSeparator()
        device_menu.addAction(self.action_firmware_upload)
        device_menu.addSeparator()
        device_menu.addAction(self.action_connect_emulator)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_toggle_theme)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.action_can_editor)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.action_about)

    def _create_toolbars(self) -> None:
        """Create toolbars - disabled to avoid duplication with screen editor toolbar."""
        # Main toolbar removed - all controls are in screen editor toolbar
        # File operations are accessible via File menu (Ctrl+N, Ctrl+O, Ctrl+S)
        # Device operations are in Device menu
        pass

    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Connection status label
        self._connection_label = QLabel("Disconnected")
        self._connection_label.setStyleSheet("color: #ff4444;")
        self.statusbar.addPermanentWidget(self._connection_label)

        # Config status label
        self._config_label = QLabel("New configuration")
        self.statusbar.addWidget(self._config_label)

    def _create_dock_widgets(self) -> None:
        """Create dock widgets."""
        # Project Tree (left dock)
        self._project_dock = QDockWidget("Project", self)
        self._project_dock.setMinimumWidth(DOCK_MIN_WIDTH)
        self._project_tree = self._create_project_tree()
        self._project_dock.setWidget(self._project_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._project_dock)

        # Note: Properties panel is integrated into ScreenEditorWidget

        # Monitor Panel (bottom dock with tabs)
        self._monitor_dock = QDockWidget("Monitor", self)
        self._monitor_panel = MonitorPanel()
        self._monitor_dock.setWidget(self._monitor_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._monitor_dock)

    def _create_project_tree(self) -> QTreeWidget:
        """Create project navigation tree."""
        tree = QTreeWidget()
        tree.setHeaderLabel("Configuration")
        tree.setIndentation(20)

        # Categories
        categories = [
            ("Display", ["Display Settings", "Brightness"]),
            ("Themes", ["Active Theme", "Custom Themes"]),
            ("Screens", ["Main Screen"]),
            ("CAN Bus", ["CAN Settings", "CAN Security"]),
            ("GPS", ["GPS Settings", "Tracks"]),
            ("Camera", ["Camera Settings", "Recording"]),
            ("Cloud", ["Cloud Telemetry"]),
            ("Voice", ["Voice Alerts"]),
            ("Logger", ["Data Logger"]),
            ("Lap Timer", ["Lap Timer Settings"]),
            ("OTA", ["Update Settings"]),
            ("WiFi", ["WiFi Settings"]),
        ]

        for category, items in categories:
            parent = QTreeWidgetItem(tree, [category])
            parent.setExpanded(False)
            for item in items:
                child = QTreeWidgetItem(parent, [item])

        tree.itemClicked.connect(self._on_tree_item_clicked)
        return tree

    def _create_central_widget(self) -> None:
        """Create central widget with screen editor."""
        self._screen_editor = ScreenEditorWidget()
        self.setCentralWidget(self._screen_editor)

    def _sync_screens_to_editor(self) -> None:
        """Sync screens from config to editor."""
        if self._config_manager.has_config:
            screens = self._config_manager.config.screens
            self._screen_editor.set_screens(screens)

    def _sync_screens_from_editor(self) -> None:
        """Sync screens from editor to config."""
        if self._config_manager.has_config:
            self._config_manager.config.screens = self._screen_editor.get_screens()
            self._config_manager.mark_modified()

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Device controller signals
        self._device_controller.connected.connect(self._on_device_connected)
        self._device_controller.disconnected.connect(self._on_device_disconnected)
        self._device_controller.error_occurred.connect(self._on_device_error)
        self._device_controller.telemetry_received.connect(self._on_telemetry_received)

        # Config manager callbacks
        self._config_manager.add_change_callback(self._on_config_changed)

        # Screen editor signals
        self._screen_editor.screen_changed.connect(self._sync_screens_from_editor)

    def _restore_state(self) -> None:
        """Restore window state from settings."""
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)

    def _save_state(self) -> None:
        """Save window state to settings."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())

    def _update_title(self) -> None:
        """Update window title."""
        title = f"{APP_NAME} v{APP_VERSION}"

        if self._config_manager.has_config:
            name = self._config_manager.config.name
            if self._config_manager.is_modified:
                name += " *"
            title = f"{name} - {title}"

        self.setWindowTitle(title)

    # --- Slots ---

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle project tree item click."""
        item_text = item.text(0)
        logger.debug(f"Tree item clicked: {item_text}")

        # Check if this item has an associated dialog
        if has_dialog(item_text):
            # Update dialog factory with current config
            if self._config_manager.has_config:
                self._dialog_factory.set_config(self._config_manager.config)
                if self._dialog_factory.show_dialog_for_item(item_text):
                    # Dialog was shown and may have modified settings
                    self._config_manager.mark_modified()
                    self._update_title()
        else:
            self.statusbar.showMessage(f"Selected: {item_text}", 3000)

    def _on_device_connected(self) -> None:
        """Handle device connected."""
        self._connection_label.setText("Connected")
        self._connection_label.setStyleSheet("color: #44ff44;")
        self.action_disconnect.setEnabled(True)
        self.action_connect.setEnabled(False)
        self.action_read_config.setEnabled(True)
        self.action_write_config.setEnabled(True)
        self._monitor_panel.set_connected(True)
        self._monitor_panel.add_log("info", "Device connected")
        self.statusbar.showMessage("Device connected", 3000)

    def _on_device_disconnected(self) -> None:
        """Handle device disconnected."""
        self._connection_label.setText("Disconnected")
        self._connection_label.setStyleSheet("color: #ff4444;")
        self.action_disconnect.setEnabled(False)
        self.action_connect.setEnabled(True)
        self.action_read_config.setEnabled(False)
        self.action_write_config.setEnabled(False)
        self._monitor_panel.set_connected(False)
        self._monitor_panel.add_log("info", "Device disconnected")
        self.statusbar.showMessage("Device disconnected", 3000)

    def _on_device_error(self, message: str) -> None:
        """Handle device error."""
        logger.error(f"Device error: {message}")
        self._monitor_panel.add_log("error", message)
        self.statusbar.showMessage(f"Error: {message}", 5000)

    def _on_telemetry_received(self, packet) -> None:
        """Handle telemetry data."""
        # Update monitor panel with telemetry
        if hasattr(packet, 'telemetry') and packet.telemetry:
            self._monitor_panel.update_telemetry(packet.telemetry)
        if hasattr(packet, 'can_messages') and packet.can_messages:
            for msg in packet.can_messages:
                self._monitor_panel.add_can_message(msg.id, msg.data)
        if hasattr(packet, 'gps') and packet.gps:
            self._monitor_panel.update_gps(packet.gps)

    def _on_config_changed(self) -> None:
        """Handle configuration change."""
        self._update_title()

    # --- Actions ---

    def new_configuration(self) -> None:
        """Create new configuration."""
        if self._config_manager.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save changes before creating a new configuration?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_configuration():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # Show template selection dialog
        template = show_template_dialog(self)

        if template:
            # Create new config with template
            self._config_manager.new_configuration()

            # Apply template screens
            if template.screens:
                self._config_manager.config.screens = template.screens.copy()

            self._sync_screens_to_editor()
            self.statusbar.showMessage(f"Created from template: {template.name}", 3000)
        else:
            # User cancelled - create empty config
            self._config_manager.new_configuration()
            self._sync_screens_to_editor()
            self.statusbar.showMessage("New configuration created", 3000)

    def open_configuration(self, file_path: str = None) -> None:
        """Open configuration file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Configuration",
                "", f"Racing Dashboard Config (*{CONFIG_EXTENSION});;All Files (*)"
            )

        if file_path:
            try:
                self._config_manager.load_from_file(file_path)
                self._sync_screens_to_editor()
                self.statusbar.showMessage(f"Opened: {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def save_configuration(self) -> bool:
        """Save configuration."""
        if self._config_manager.file_path:
            try:
                self._config_manager.save_to_file()
                self.statusbar.showMessage("Configuration saved", 3000)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
                return False
        else:
            return self.save_configuration_as()

    def save_configuration_as(self) -> bool:
        """Save configuration with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration",
            "", f"Racing Dashboard Config (*{CONFIG_EXTENSION});;All Files (*)"
        )

        if file_path:
            if not file_path.endswith(CONFIG_EXTENSION):
                file_path += CONFIG_EXTENSION
            try:
                self._config_manager.save_to_file(file_path)
                self.statusbar.showMessage(f"Saved: {file_path}", 3000)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

        return False

    def export_for_device_json(self) -> None:
        """Export configuration as optimized JSON for device."""
        if not self._config_manager.has_config:
            QMessageBox.warning(self, "No Configuration", "No configuration to export")
            return

        # Sync screens from editor
        self._sync_screens_from_editor()

        # Validate first
        exporter = ConfigExporter(self._config_manager.config)
        is_valid, errors, warnings = exporter.validate()

        # Show warnings if any
        if warnings:
            warning_msg = "Validation warnings:\n\n" + "\n".join(f"• {w}" for w in warnings)
            QMessageBox.warning(self, "Validation Warnings", warning_msg)

        if not is_valid:
            error_msg = "Configuration has errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            QMessageBox.critical(self, "Validation Failed", error_msg)
            return

        # Ask for file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export for Device",
            "dashboard_config.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            result = exporter.export_json(file_path, compact=True)

            if result.success:
                QMessageBox.information(
                    self, "Export Successful",
                    f"Configuration exported successfully!\n\n"
                    f"File: {result.file_path}\n"
                    f"Size: {result.file_size} bytes\n"
                    f"Checksum: {result.checksum[:16]}..."
                )
                self.statusbar.showMessage(f"Exported: {file_path}", 3000)
            else:
                error_msg = "Export failed:\n\n" + "\n".join(result.errors)
                QMessageBox.critical(self, "Export Failed", error_msg)

    def export_for_device_binary(self) -> None:
        """Export configuration as binary format for device."""
        if not self._config_manager.has_config:
            QMessageBox.warning(self, "No Configuration", "No configuration to export")
            return

        # Sync screens from editor
        self._sync_screens_from_editor()

        # Validate first
        exporter = ConfigExporter(self._config_manager.config)
        is_valid, errors, warnings = exporter.validate()

        if warnings:
            warning_msg = "Validation warnings:\n\n" + "\n".join(f"• {w}" for w in warnings)
            QMessageBox.warning(self, "Validation Warnings", warning_msg)

        if not is_valid:
            error_msg = "Configuration has errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            QMessageBox.critical(self, "Validation Failed", error_msg)
            return

        # Ask for file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Binary",
            "dashboard_config.bin",
            "Binary Files (*.bin);;All Files (*)"
        )

        if file_path:
            result = exporter.export_binary(file_path)

            if result.success:
                QMessageBox.information(
                    self, "Export Successful",
                    f"Binary configuration exported!\n\n"
                    f"File: {result.file_path}\n"
                    f"Size: {result.file_size} bytes\n"
                    f"CRC32: {result.checksum}"
                )
                self.statusbar.showMessage(f"Binary exported: {file_path}", 3000)
            else:
                error_msg = "Export failed:\n\n" + "\n".join(result.errors)
                QMessageBox.critical(self, "Export Failed", error_msg)

    def show_connect_dialog(self) -> None:
        """Show device connection dialog."""
        # Simple port selection for now
        ports = self._device_controller.list_serial_ports()

        if not ports:
            QMessageBox.warning(self, "No Devices", "No serial ports found.")
            return

        # For now, just connect to first port
        port = ports[0].port
        if self._device_controller.connect_serial(port):
            logger.info(f"Connected to {port}")
        else:
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to {port}")

    def disconnect_device(self) -> None:
        """Disconnect from device."""
        self._device_controller.disconnect()

    def connect_emulator(self) -> None:
        """Connect to emulator."""
        if self._device_controller.connect_emulator():
            logger.info("Connected to emulator")
        else:
            QMessageBox.critical(self, "Connection Failed", "Failed to connect to emulator")

    def read_from_device(self) -> None:
        """Read configuration from device."""
        config_data = self._device_controller.read_configuration()
        if config_data:
            try:
                self._config_manager.load_from_dict(
                    __import__('json').loads(config_data.decode('utf-8'))
                )
                self.statusbar.showMessage("Configuration read from device", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to parse configuration:\n{e}")
        else:
            QMessageBox.warning(self, "Error", "Failed to read configuration from device")

    def write_to_device(self) -> None:
        """Write configuration to device."""
        if not self._config_manager.has_config:
            QMessageBox.warning(self, "No Configuration", "No configuration to write")
            return

        config_data = self._config_manager.export_for_device()
        if self._device_controller.write_configuration(config_data):
            self.statusbar.showMessage("Configuration written to device", 3000)
        else:
            QMessageBox.critical(self, "Error", "Failed to write configuration to device")

    def toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            self._theme_manager.toggle_theme(app)

    def show_can_editor(self) -> None:
        """Show CAN message editor dialog."""
        # Get current CAN database from config
        can_db = None
        if self._config_manager.has_config:
            can_db = getattr(self._config_manager.config, 'can_database', None)

        # Show editor
        result = show_can_editor(can_db, self)

        if result:
            # Save updated database to config
            if self._config_manager.has_config:
                self._config_manager.config.can_database = result
                self._config_manager.mark_modified()
                self.statusbar.showMessage(f"CAN database updated: {len(result.messages)} messages", 3000)

    def show_firmware_dialog(self) -> None:
        """Show firmware upload dialog."""
        show_firmware_dialog(self._device_controller, self)

    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>Racing Dashboard Configuration Tool</p>"
            f"<p>Configure device settings and design screen layouts.</p>"
        )

    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self._config_manager.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save changes before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_configuration():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # Disconnect device
        if self._device_controller.is_connected:
            self._device_controller.disconnect()

        # Save window state
        self._save_state()

        event.accept()
