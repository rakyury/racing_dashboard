# CAN Settings Dialog
"""Dialog for configuring CAN bus settings."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import CANSettings, CANSecuritySettings


CAN_BAUDRATES = [
    "125000",
    "250000",
    "500000",
    "1000000",
]

CAN_FD_BAUDRATES = [
    "1000000",
    "2000000",
    "5000000",
    "8000000",
]

SECURITY_MODES = [
    ("Disabled", "disabled"),
    ("MAC Only", "mac_only"),
    ("Encrypt + MAC", "encrypt_mac"),
    ("Encrypt + Sign", "encrypt_sign"),
]


class CANSettingsDialog(BaseSettingsDialog):
    """Dialog for CAN bus settings."""

    def __init__(self, can_settings: CANSettings, parent=None):
        self._settings = can_settings
        super().__init__("CAN Bus Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # CAN Bus Group
        can_group = self._create_group("CAN Bus Configuration")
        can_layout = QVBoxLayout(can_group)
        can_layout.setContentsMargins(12, 20, 12, 12)
        can_layout.setSpacing(8)

        # Enable CAN
        self._enabled = self._create_checkbox("Enable CAN bus", True)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        can_layout.addWidget(self._enabled)

        # Baudrate
        self._baudrate_combo = self._create_combobox(CAN_BAUDRATES, "500000")
        can_layout.addWidget(SettingsRow(
            "Baudrate:",
            self._baudrate_combo,
            "Standard CAN bus speed"
        ))

        self._content_layout.addWidget(can_group)

        # CAN FD Group
        fd_group = self._create_group("CAN FD (Flexible Data-rate)")
        fd_layout = QVBoxLayout(fd_group)
        fd_layout.setContentsMargins(12, 20, 12, 12)
        fd_layout.setSpacing(8)

        # Enable CAN FD
        self._fd_enabled = self._create_checkbox("Enable CAN FD", False)
        self._fd_enabled.stateChanged.connect(self._on_fd_enabled_changed)
        fd_layout.addWidget(self._fd_enabled)

        # FD Baudrate
        self._fd_baudrate_combo = self._create_combobox(CAN_FD_BAUDRATES, "5000000")
        self._fd_baudrate_combo.setEnabled(False)
        fd_layout.addWidget(SettingsRow(
            "FD Baudrate:",
            self._fd_baudrate_combo,
            "CAN FD data phase speed"
        ))

        self._content_layout.addWidget(fd_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle CAN enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._baudrate_combo.setEnabled(enabled)
        self._fd_enabled.setEnabled(enabled)
        if enabled:
            self._on_fd_enabled_changed(self._fd_enabled.checkState().value)
        else:
            self._fd_baudrate_combo.setEnabled(False)

    def _on_fd_enabled_changed(self, state: int) -> None:
        """Handle CAN FD enable toggle."""
        enabled = state == Qt.CheckState.Checked.value and self._enabled.isChecked()
        self._fd_baudrate_combo.setEnabled(enabled)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)
        self._baudrate_combo.setCurrentText(str(self._settings.baudrate))
        self._fd_enabled.setChecked(self._settings.fd_enabled)
        self._fd_baudrate_combo.setCurrentText(str(self._settings.fd_baudrate))

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()
        self._settings.baudrate = int(self._baudrate_combo.currentText())
        self._settings.fd_enabled = self._fd_enabled.isChecked()
        self._settings.fd_baudrate = int(self._fd_baudrate_combo.currentText())

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._baudrate_combo.setCurrentText("500000")
        self._fd_enabled.setChecked(False)
        self._fd_baudrate_combo.setCurrentText("5000000")


class CANSecurityDialog(BaseSettingsDialog):
    """Dialog for CAN security settings."""

    def __init__(self, settings: CANSecuritySettings, parent=None):
        self._settings = settings
        super().__init__("CAN Security Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Security Mode Group
        security_group = self._create_group("Security Mode")
        security_layout = QVBoxLayout(security_group)
        security_layout.setContentsMargins(12, 20, 12, 12)
        security_layout.setSpacing(8)

        # Security mode
        mode_names = [m[0] for m in SECURITY_MODES]
        self._mode_combo = self._create_combobox(mode_names, "Disabled")
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        security_layout.addWidget(SettingsRow(
            "Security Mode:",
            self._mode_combo,
            "CAN message security level"
        ))

        # Description label
        self._mode_desc = QLabel("No security applied to CAN messages")
        self._mode_desc.setStyleSheet("color: #888; font-size: 11px; padding: 8px;")
        self._mode_desc.setWordWrap(True)
        security_layout.addWidget(self._mode_desc)

        self._content_layout.addWidget(security_group)

        # Protection Group
        protection_group = self._create_group("Protection Features")
        protection_layout = QVBoxLayout(protection_group)
        protection_layout.setContentsMargins(12, 20, 12, 12)
        protection_layout.setSpacing(8)

        # Replay protection
        self._replay_protection = self._create_checkbox("Replay attack protection", True)
        protection_layout.addWidget(SettingsRow(
            "",
            self._replay_protection,
            "Prevent replay of captured CAN messages"
        ))

        # Intrusion detection
        self._intrusion_detection = self._create_checkbox("Intrusion detection", True)
        protection_layout.addWidget(SettingsRow(
            "",
            self._intrusion_detection,
            "Detect unauthorized CAN messages"
        ))

        self._content_layout.addWidget(protection_group)

        # Key Management Group
        key_group = self._create_group("Key Management")
        key_layout = QVBoxLayout(key_group)
        key_layout.setContentsMargins(12, 20, 12, 12)
        key_layout.setSpacing(8)

        # Key rotation interval
        self._key_rotation_spin = self._create_spinbox(60, 86400, 3600, "sec")
        key_layout.addWidget(SettingsRow(
            "Key Rotation:",
            self._key_rotation_spin,
            "Interval for automatic key rotation"
        ))

        self._content_layout.addWidget(key_group)

    def _on_mode_changed(self, mode: str) -> None:
        """Update description based on mode."""
        descriptions = {
            "Disabled": "No security applied to CAN messages",
            "MAC Only": "Message authentication code added to verify integrity",
            "Encrypt + MAC": "Messages encrypted and authenticated",
            "Encrypt + Sign": "Full encryption with digital signature",
        }
        self._mode_desc.setText(descriptions.get(mode, ""))

        # Enable/disable security options
        enabled = mode != "Disabled"
        self._replay_protection.setEnabled(enabled)
        self._intrusion_detection.setEnabled(enabled)
        self._key_rotation_spin.setEnabled(enabled)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        # Find display name for mode
        for display_name, internal_name in SECURITY_MODES:
            if internal_name == self._settings.mode:
                self._mode_combo.setCurrentText(display_name)
                break

        self._replay_protection.setChecked(self._settings.replay_protection)
        self._intrusion_detection.setChecked(self._settings.intrusion_detection)
        self._key_rotation_spin.setValue(self._settings.key_rotation_interval)

        self._on_mode_changed(self._mode_combo.currentText())

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        mode_display = self._mode_combo.currentText()
        for display_name, internal_name in SECURITY_MODES:
            if display_name == mode_display:
                self._settings.mode = internal_name
                break

        self._settings.replay_protection = self._replay_protection.isChecked()
        self._settings.intrusion_detection = self._intrusion_detection.isChecked()
        self._settings.key_rotation_interval = self._key_rotation_spin.value()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._mode_combo.setCurrentText("Disabled")
        self._replay_protection.setChecked(True)
        self._intrusion_detection.setChecked(True)
        self._key_rotation_spin.setValue(3600)
