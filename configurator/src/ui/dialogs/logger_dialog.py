# Data Logger Dialog
"""Dialog for configuring data logger settings."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import LoggerSettings


LOG_FORMATS = [
    ("CSV (Text)", "csv"),
    ("Binary", "binary"),
    ("Compressed (Zlib)", "compressed"),
    ("Parquet", "parquet"),
]

TRIGGER_MODES = [
    ("Manual", "manual"),
    ("Ignition On", "ignition"),
    ("Speed Threshold", "speed"),
    ("Always", "always"),
]

SAMPLE_RATES = ["10", "20", "50", "100", "200", "500"]


class LoggerSettingsDialog(BaseSettingsDialog):
    """Dialog for data logger settings."""

    def __init__(self, settings: LoggerSettings, parent=None):
        self._settings = settings
        super().__init__("Data Logger Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Logger Configuration Group
        logger_group = self._create_group("Logger Configuration")
        logger_layout = QVBoxLayout(logger_group)
        logger_layout.setContentsMargins(12, 20, 12, 12)
        logger_layout.setSpacing(8)

        # Enable logger
        self._enabled = self._create_checkbox("Enable data logging", True)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        logger_layout.addWidget(self._enabled)

        # Format
        format_names = [f[0] for f in LOG_FORMATS]
        self._format_combo = self._create_combobox(format_names, "Compressed (Zlib)")
        logger_layout.addWidget(SettingsRow(
            "Format:",
            self._format_combo,
            "Data storage format"
        ))

        # Sample rate
        self._sample_rate_combo = self._create_combobox(SAMPLE_RATES, "100")
        logger_layout.addWidget(SettingsRow(
            "Sample Rate:",
            self._sample_rate_combo,
            "Data samples per second (Hz)"
        ))

        self._content_layout.addWidget(logger_group)

        # Compression Group
        compression_group = self._create_group("Compression")
        compression_layout = QVBoxLayout(compression_group)
        compression_layout.setContentsMargins(12, 20, 12, 12)
        compression_layout.setSpacing(8)

        # Compression level slider
        compression_widget = QWidget()
        comp_layout = QHBoxLayout(compression_widget)
        comp_layout.setContentsMargins(0, 0, 0, 0)
        comp_layout.setSpacing(12)

        self._compression_slider = self._create_slider(1, 9, 6)
        self._compression_slider.valueChanged.connect(self._on_compression_changed)
        comp_layout.addWidget(self._compression_slider)

        self._compression_label = QLabel("6")
        self._compression_label.setStyleSheet("color: #fff; min-width: 20px;")
        comp_layout.addWidget(self._compression_label)

        compression_layout.addWidget(SettingsRow(
            "Level:",
            compression_widget,
            "1 = Fast, 9 = Best compression"
        ))

        self._content_layout.addWidget(compression_group)

        # Trigger Group
        trigger_group = self._create_group("Recording Trigger")
        trigger_layout = QVBoxLayout(trigger_group)
        trigger_layout.setContentsMargins(12, 20, 12, 12)
        trigger_layout.setSpacing(8)

        # Trigger mode
        trigger_names = [t[0] for t in TRIGGER_MODES]
        self._trigger_combo = self._create_combobox(trigger_names, "Ignition On")
        trigger_layout.addWidget(SettingsRow("Trigger Mode:", self._trigger_combo))

        # Pre-trigger duration
        self._pretrigger_spin = self._create_spinbox(0, 60, 10, "sec")
        trigger_layout.addWidget(SettingsRow(
            "Pre-trigger Buffer:",
            self._pretrigger_spin,
            "Seconds of data to keep before trigger"
        ))

        self._content_layout.addWidget(trigger_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle logger enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._format_combo.setEnabled(enabled)
        self._sample_rate_combo.setEnabled(enabled)
        self._compression_slider.setEnabled(enabled)
        self._trigger_combo.setEnabled(enabled)
        self._pretrigger_spin.setEnabled(enabled)

    def _on_compression_changed(self, value: int) -> None:
        """Update compression label."""
        self._compression_label.setText(str(value))

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)

        for display_name, internal_name in LOG_FORMATS:
            if internal_name == self._settings.format:
                self._format_combo.setCurrentText(display_name)
                break

        self._sample_rate_combo.setCurrentText(str(self._settings.sample_rate))
        self._compression_slider.setValue(self._settings.compression_level)
        self._compression_label.setText(str(self._settings.compression_level))

        for display_name, internal_name in TRIGGER_MODES:
            if internal_name == self._settings.trigger_mode:
                self._trigger_combo.setCurrentText(display_name)
                break

        self._pretrigger_spin.setValue(self._settings.pre_trigger_duration)

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()

        format_display = self._format_combo.currentText()
        for display_name, internal_name in LOG_FORMATS:
            if display_name == format_display:
                self._settings.format = internal_name
                break

        self._settings.sample_rate = int(self._sample_rate_combo.currentText())
        self._settings.compression_level = self._compression_slider.value()

        trigger_display = self._trigger_combo.currentText()
        for display_name, internal_name in TRIGGER_MODES:
            if display_name == trigger_display:
                self._settings.trigger_mode = internal_name
                break

        self._settings.pre_trigger_duration = self._pretrigger_spin.value()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._format_combo.setCurrentText("Compressed (Zlib)")
        self._sample_rate_combo.setCurrentText("100")
        self._compression_slider.setValue(6)
        self._trigger_combo.setCurrentText("Ignition On")
        self._pretrigger_spin.setValue(10)
