# Racing Dashboard Configurator

Desktop application for configuring Racing Dashboard devices and designing screen layouts.

## Features

- **Device Configuration**: Configure all 12 modules of Racing Dashboard
- **Screen Editor**: Visual drag-and-drop editor for designing dashboard layouts
- **Real-time Telemetry**: Monitor live data from the device
- **Multiple Connections**: USB Serial, WiFi, and Emulator modes

## Requirements

- Python 3.10+
- PyQt6 6.6.0+

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
# Run the application
python src/main.py

# With debug logging
python src/main.py --debug

# With light theme
python src/main.py --light-theme

# Connect to emulator (for development)
python src/main.py --debug
# Then use Device > Connect Emulator
```

## Project Structure

```
configurator/
├── src/
│   ├── main.py                 # Entry point
│   ├── communication/          # Device communication
│   │   ├── protocol.py         # Binary protocol
│   │   ├── transport_base.py   # Transport abstraction
│   │   ├── serial_transport.py # USB Serial
│   │   ├── emulator_transport.py # Emulator for dev
│   │   ├── comm_manager.py     # High-level API
│   │   └── telemetry.py        # Telemetry structures
│   ├── models/                 # Data models
│   │   ├── dashboard_config.py # Main configuration
│   │   ├── config_manager.py   # Config management
│   │   ├── screen_layout.py    # Screen layouts
│   │   └── widget_types.py     # Widget definitions
│   ├── controllers/            # Business logic
│   │   ├── device_controller.py # Qt-based device control
│   │   └── transport.py        # Transport factory
│   ├── ui/                     # User interface
│   │   ├── main_window.py      # Main window
│   │   ├── dialogs/            # Configuration dialogs
│   │   ├── widgets/            # Custom widgets
│   │   ├── mixins/             # Window mixins
│   │   └── screen_editor/      # Visual editor
│   └── utils/                  # Utilities
│       ├── logger.py           # Logging setup
│       ├── constants.py        # Constants
│       └── theme.py            # Theme management
├── resources/                  # Assets
├── tests/                      # Unit tests
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## Architecture

Based on PMU_30 Configurator:

- **MVC Pattern**: Models, Views, Controllers separation
- **Mixins**: Modular window functionality
- **Factory Pattern**: Dialog and transport creation
- **Signal-Slot**: Qt event handling
- **Binary Protocol**: Efficient device communication

## Configuration Format

Configuration files use JSON format (`.rdconfig`):

```json
{
  "version": "1.0",
  "name": "My Racing Dashboard",
  "display": {
    "profile": "1024x600",
    "brightness_max": 700
  },
  "theme": {
    "active_preset": "Motec Dark"
  },
  "screens": [
    {
      "name": "Main Screen",
      "widgets": [...]
    }
  ]
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Building Executable

```bash
python build_exe.py
```

## License

MIT License
