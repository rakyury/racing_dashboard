# Configuration Manager
"""Manages loading, saving, and validation of dashboard configurations."""

import json
import logging
from pathlib import Path
from typing import Optional, Callable, List
from datetime import datetime

from .dashboard_config import DashboardConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages dashboard configuration lifecycle.
    Handles file I/O, validation, and change tracking.
    """

    def __init__(self):
        self._config: Optional[DashboardConfig] = None
        self._file_path: Optional[Path] = None
        self._is_modified: bool = False
        self._change_callbacks: List[Callable] = []

    @property
    def config(self) -> Optional[DashboardConfig]:
        """Get the current configuration."""
        return self._config

    @property
    def file_path(self) -> Optional[Path]:
        """Get the current file path."""
        return self._file_path

    @property
    def is_modified(self) -> bool:
        """Check if configuration has unsaved changes."""
        return self._is_modified

    @property
    def has_config(self) -> bool:
        """Check if a configuration is loaded."""
        return self._config is not None

    def new_configuration(self, name: str = "Untitled Project") -> DashboardConfig:
        """Create a new empty configuration."""
        self._config = DashboardConfig(name=name)
        self._file_path = None
        self._is_modified = False
        self._notify_change()
        logger.info(f"Created new configuration: {name}")
        return self._config

    def load_from_file(self, file_path: str) -> DashboardConfig:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to the configuration file

        Returns:
            Loaded DashboardConfig

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
            ValueError: If configuration format is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        logger.info(f"Loading configuration from: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate version
        version = data.get("version", "1.0")
        if not self._is_version_compatible(version):
            raise ValueError(f"Incompatible configuration version: {version}")

        self._config = DashboardConfig.from_dict(data)
        self._file_path = path
        self._is_modified = False
        self._notify_change()

        logger.info(f"Configuration loaded: {self._config.name}")
        return self._config

    def load_from_dict(self, data: dict) -> DashboardConfig:
        """
        Load configuration from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Loaded DashboardConfig
        """
        self._config = DashboardConfig.from_dict(data)
        self._file_path = None
        self._is_modified = True
        self._notify_change()
        return self._config

    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            file_path: Path to save to (uses current path if None)

        Returns:
            True if save successful
        """
        if self._config is None:
            logger.error("No configuration to save")
            return False

        path = Path(file_path) if file_path else self._file_path
        if path is None:
            logger.error("No file path specified")
            return False

        logger.info(f"Saving configuration to: {path}")

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Update modified timestamp
        self._config.modified = datetime.now().isoformat()

        # Write to file
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._config.to_dict(), f, indent=2)

        self._file_path = path
        self._is_modified = False
        self._notify_change()

        logger.info(f"Configuration saved: {self._config.name}")
        return True

    def export_for_device(self) -> bytes:
        """
        Export configuration in binary format for device.

        Returns:
            Binary configuration data
        """
        if self._config is None:
            raise ValueError("No configuration to export")

        # For now, just export as JSON bytes
        # In the future, this could be a more compact binary format
        json_str = self._config.to_json()
        return json_str.encode('utf-8')

    def mark_modified(self) -> None:
        """Mark configuration as having unsaved changes."""
        self._is_modified = True
        self._notify_change()

    def add_change_callback(self, callback: Callable) -> None:
        """Add a callback for configuration changes."""
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable) -> None:
        """Remove a change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def _notify_change(self) -> None:
        """Notify all listeners of configuration change."""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

    def _is_version_compatible(self, version: str) -> bool:
        """Check if a configuration version is compatible."""
        try:
            major, minor = map(int, version.split('.')[:2])
            # Compatible with 1.x versions
            return major == 1
        except (ValueError, AttributeError):
            return False

    def get_config_summary(self) -> dict:
        """Get a summary of the current configuration."""
        if self._config is None:
            return {}

        return {
            "name": self._config.name,
            "version": self._config.version,
            "screens": len(self._config.screens),
            "widgets": sum(len(s.widgets) for s in self._config.screens),
            "display_profile": self._config.display.profile,
            "theme": self._config.theme.active_preset,
            "modified": self._is_modified,
            "file_path": str(self._file_path) if self._file_path else None,
        }

    def validate_config(self) -> tuple:
        """
        Validate the current configuration.

        Returns:
            Tuple of (is_valid, list of errors/warnings)
        """
        if self._config is None:
            return (False, ["No configuration loaded"])

        errors = []
        warnings = []

        # Validate screens
        if len(self._config.screens) == 0:
            errors.append("Configuration must have at least one screen")

        for i, screen in enumerate(self._config.screens):
            # Check for widgets outside screen bounds
            for widget in screen.widgets:
                if widget.x < 0 or widget.y < 0:
                    warnings.append(f"Screen '{screen.name}': Widget '{widget.name}' has negative position")
                if widget.x + widget.width > screen.width:
                    warnings.append(f"Screen '{screen.name}': Widget '{widget.name}' extends beyond screen width")
                if widget.y + widget.height > screen.height:
                    warnings.append(f"Screen '{screen.name}': Widget '{widget.name}' extends beyond screen height")

        # Validate CAN settings
        if self._config.can.enabled:
            if self._config.can.baudrate not in [125000, 250000, 500000, 1000000]:
                warnings.append(f"Non-standard CAN baudrate: {self._config.can.baudrate}")

        # Validate GPS settings
        if self._config.gps.enabled:
            if self._config.gps.update_rate > 50:
                warnings.append(f"High GPS update rate may reduce accuracy: {self._config.gps.update_rate} Hz")

        is_valid = len(errors) == 0
        messages = errors + warnings
        return (is_valid, messages)
