# OTA Update Dialog
"""Dialog for configuring OTA update settings."""

from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import OTASettings


CHECK_INTERVALS = ["1", "6", "12", "24", "48", "168"]
INTERVAL_LABELS = ["1 hour", "6 hours", "12 hours", "24 hours", "2 days", "1 week"]


class OTASettingsDialog(BaseSettingsDialog):
    """Dialog for OTA update settings."""

    def __init__(self, settings: OTASettings, parent=None):
        self._settings = settings
        super().__init__("OTA Update Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # OTA Configuration Group
        ota_group = self._create_group("Update Configuration")
        ota_layout = QVBoxLayout(ota_group)
        ota_layout.setContentsMargins(12, 20, 12, 12)
        ota_layout.setSpacing(8)

        # Enable OTA
        self._enabled = self._create_checkbox("Enable OTA updates", True)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        ota_layout.addWidget(self._enabled)

        # Auto check
        self._auto_check = self._create_checkbox("Automatically check for updates", True)
        ota_layout.addWidget(self._auto_check)

        # Check interval
        self._interval_combo = self._create_combobox(INTERVAL_LABELS, "24 hours")
        ota_layout.addWidget(SettingsRow("Check Interval:", self._interval_combo))

        self._content_layout.addWidget(ota_group)

        # Beta Channel Group
        beta_group = self._create_group("Beta Channel")
        beta_layout = QVBoxLayout(beta_group)
        beta_layout.setContentsMargins(12, 20, 12, 12)
        beta_layout.setSpacing(8)

        # Allow beta
        self._allow_beta = self._create_checkbox("Allow beta updates", False)
        beta_layout.addWidget(SettingsRow(
            "",
            self._allow_beta,
            "Receive early access to new features (may be unstable)"
        ))

        self._content_layout.addWidget(beta_group)

        # Server Group
        server_group = self._create_group("Update Server")
        server_layout = QVBoxLayout(server_group)
        server_layout.setContentsMargins(12, 20, 12, 12)
        server_layout.setSpacing(8)

        # Server URL
        self._server_edit = self._create_lineedit("", "https://updates.example.com")
        server_layout.addWidget(SettingsRow(
            "Server URL:",
            self._server_edit,
            "Leave empty to use default server"
        ))

        self._content_layout.addWidget(server_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle OTA enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._auto_check.setEnabled(enabled)
        self._interval_combo.setEnabled(enabled)
        self._allow_beta.setEnabled(enabled)
        self._server_edit.setEnabled(enabled)

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)
        self._auto_check.setChecked(self._settings.auto_check)

        # Find interval label
        interval_str = str(self._settings.check_interval)
        for i, val in enumerate(CHECK_INTERVALS):
            if val == interval_str:
                self._interval_combo.setCurrentText(INTERVAL_LABELS[i])
                break

        self._allow_beta.setChecked(self._settings.allow_beta)
        self._server_edit.setText(self._settings.server_url)

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()
        self._settings.auto_check = self._auto_check.isChecked()

        # Get interval value
        interval_label = self._interval_combo.currentText()
        for i, label in enumerate(INTERVAL_LABELS):
            if label == interval_label:
                self._settings.check_interval = int(CHECK_INTERVALS[i])
                break

        self._settings.allow_beta = self._allow_beta.isChecked()
        self._settings.server_url = self._server_edit.text()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._auto_check.setChecked(True)
        self._interval_combo.setCurrentText("24 hours")
        self._allow_beta.setChecked(False)
        self._server_edit.setText("")
