#!/usr/bin/env python3
# Racing Dashboard Configurator - Main Entry Point
"""
Racing Dashboard Configurator

Desktop application for configuring Racing Dashboard devices and
designing screen layouts with a visual drag-and-drop editor.

Usage:
    python main.py [--debug] [--light-theme]
"""

import sys
import argparse
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging, get_logger
from utils.theme import ThemeManager
from utils.constants import APP_NAME, APP_VERSION, ORGANIZATION
from ui.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Racing Dashboard Configurator"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--light-theme",
        action="store_true",
        help="Use light theme instead of dark"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Open configuration file on startup"
    )
    return parser.parse_args()


def main() -> int:
    """Application entry point."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    logger = get_logger(__name__)

    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)

    # Set application info
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)
    QCoreApplication.setOrganizationName(ORGANIZATION)

    # Set application icon
    icon_path = Path(__file__).parent.parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Apply theme
    theme_manager = ThemeManager()
    if args.light_theme:
        theme_manager.apply_light_theme(app)
    else:
        theme_manager.apply_dark_theme(app)

    # Create main window
    main_window = MainWindow(theme_manager)

    # Open config file if specified
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            main_window.open_configuration(str(config_path))
        else:
            logger.warning(f"Config file not found: {args.config}")

    # Show window
    main_window.show()

    logger.info("Application started successfully")

    # Run event loop
    exit_code = app.exec()

    logger.info(f"Application exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
