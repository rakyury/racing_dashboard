# Voice Alerts Dialog
"""Dialog for configuring voice alerts settings."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

from .base_dialog import BaseSettingsDialog, SettingsRow
from models.dashboard_config import VoiceSettings


TTS_ENGINES = [
    ("Google TTS", "google_tts"),
    ("eSpeak", "espeak"),
    ("Flite", "flite"),
    ("Pre-recorded", "prerecorded"),
]

LANGUAGES = [
    ("English (US)", "en_us"),
    ("English (UK)", "en_gb"),
    ("German", "de_de"),
    ("French", "fr_fr"),
    ("Spanish", "es_es"),
    ("Italian", "it_it"),
]

AUDIO_OUTPUTS = [
    ("Bluetooth", "bluetooth"),
    ("Built-in Speaker", "speaker"),
    ("Headphone Jack", "headphone"),
]


class VoiceSettingsDialog(BaseSettingsDialog):
    """Dialog for voice alerts settings."""

    def __init__(self, settings: VoiceSettings, parent=None):
        self._settings = settings
        super().__init__("Voice Alerts Settings", parent)
        self._load_settings()

    def _create_content(self) -> None:
        """Create dialog content."""
        # Voice Configuration Group
        voice_group = self._create_group("Voice Configuration")
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setContentsMargins(12, 20, 12, 12)
        voice_layout.setSpacing(8)

        # Enable voice
        self._enabled = self._create_checkbox("Enable voice alerts", True)
        self._enabled.stateChanged.connect(self._on_enabled_changed)
        voice_layout.addWidget(self._enabled)

        # TTS Engine
        engine_names = [e[0] for e in TTS_ENGINES]
        self._engine_combo = self._create_combobox(engine_names, "eSpeak")
        voice_layout.addWidget(SettingsRow("TTS Engine:", self._engine_combo))

        # Language
        lang_names = [l[0] for l in LANGUAGES]
        self._language_combo = self._create_combobox(lang_names, "English (US)")
        voice_layout.addWidget(SettingsRow("Language:", self._language_combo))

        self._content_layout.addWidget(voice_group)

        # Audio Output Group
        output_group = self._create_group("Audio Output")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(12, 20, 12, 12)
        output_layout.setSpacing(8)

        # Output
        output_names = [o[0] for o in AUDIO_OUTPUTS]
        self._output_combo = self._create_combobox(output_names, "Bluetooth")
        output_layout.addWidget(SettingsRow("Output:", self._output_combo))

        # Volume slider
        volume_widget = QWidget()
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(12)

        self._volume_slider = self._create_slider(0, 100, 75)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self._volume_slider)

        self._volume_label = QLabel("75%")
        self._volume_label.setStyleSheet("color: #fff; min-width: 40px;")
        volume_layout.addWidget(self._volume_label)

        output_layout.addWidget(SettingsRow("Volume:", volume_widget))

        self._content_layout.addWidget(output_group)

    def _on_enabled_changed(self, state: int) -> None:
        """Handle voice enable toggle."""
        enabled = state == Qt.CheckState.Checked.value
        self._engine_combo.setEnabled(enabled)
        self._language_combo.setEnabled(enabled)
        self._output_combo.setEnabled(enabled)
        self._volume_slider.setEnabled(enabled)

    def _on_volume_changed(self, value: int) -> None:
        """Update volume label."""
        self._volume_label.setText(f"{value}%")

    def _load_settings(self) -> None:
        """Load settings into UI."""
        self._enabled.setChecked(self._settings.enabled)

        for display_name, internal_name in TTS_ENGINES:
            if internal_name == self._settings.engine:
                self._engine_combo.setCurrentText(display_name)
                break

        for display_name, internal_name in LANGUAGES:
            if internal_name == self._settings.language:
                self._language_combo.setCurrentText(display_name)
                break

        for display_name, internal_name in AUDIO_OUTPUTS:
            if internal_name == self._settings.output:
                self._output_combo.setCurrentText(display_name)
                break

        self._volume_slider.setValue(self._settings.volume)
        self._volume_label.setText(f"{self._settings.volume}%")

        self._on_enabled_changed(Qt.CheckState.Checked.value if self._settings.enabled else 0)

    def _apply_settings(self) -> None:
        """Apply settings from UI."""
        self._settings.enabled = self._enabled.isChecked()

        engine_display = self._engine_combo.currentText()
        for display_name, internal_name in TTS_ENGINES:
            if display_name == engine_display:
                self._settings.engine = internal_name
                break

        lang_display = self._language_combo.currentText()
        for display_name, internal_name in LANGUAGES:
            if display_name == lang_display:
                self._settings.language = internal_name
                break

        output_display = self._output_combo.currentText()
        for display_name, internal_name in AUDIO_OUTPUTS:
            if display_name == output_display:
                self._settings.output = internal_name
                break

        self._settings.volume = self._volume_slider.value()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        self._enabled.setChecked(True)
        self._engine_combo.setCurrentText("eSpeak")
        self._language_combo.setCurrentText("English (US)")
        self._output_combo.setCurrentText("Bluetooth")
        self._volume_slider.setValue(75)
