# PitaEEGLSL

PitaEEG LSL for Python (`pitaeeg` package)

[![Maintainability](https://qlty.sh/badges/40b7ffbe-a622-4a60-9190-d2545314f095/maintainability.svg)](https://qlty.sh/gh/pgv-inc/projects/PitaEEGLSL)
[![Code Coverage](https://qlty.sh/badges/40b7ffbe-a622-4a60-9190-d2545314f095/coverage.svg)](https://qlty.sh/gh/pgv-inc/projects/PitaEEGLSL)
[![Python check](https://github.com/pgv-inc/PitaEEGLSL/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/pgv-inc/PitaEEGLSL/actions/workflows/pythonpackage.yml)

## Features

- Easy-to-use Python interface for PitaEEGSensor
- Automatic platform detection and native library loading
- Context manager support for safe resource management
- Type hints for better IDE support
- Comprehensive error handling with custom exceptions

## Requirements

- make >=4.3
- Python >3.11, <4.0
- Poetry >=2.1

## Installation

- Poetry(pyproject.toml)

```toml
pitaeeg = {git = "https://github.com/pgv-inc/PitaEEGLSL.git", rev = "0.5.0"}
```

```bash
poetry install
```

- pip

```bash
pip install git+https://github.com/pgv-inc/PitaEEGLSL.git@0.5.0
```

### Native Library Setup

The native API library must be placed in the `libs/` directory according to your platform:

```bash
libs/
├── linux/
│   └── libpitaeeg.so (or libpitaeeg.so.x.x.x)
├── macos/
│   ├── arm64/
│   │   └── libpitaeeg.dylib (or libpitaeeg.x.x.x.dylib)
│   └── x86_64/
│       └── libpitaeeg.dylib (or libpitaeeg.x.x.x.dylib)
└── windows/
    └── pitaeeg.dll (or pitaeeg.dll)
```

The library will be automatically loaded from the appropriate platform directory.

## Usage

### Basic Example

```python
from pitaeeg import Sensor

# Initialize and connect to sensor
with Sensor(port="COM3") as sensor:
    # Scan and connect to device
    sensor.connect("HARU2-001", scan_timeout=10.0)
    
    # Start measurement
    devicetime_ms = sensor.start_measurement()
    
    # Receive data
    for data in sensor.receive_data():
        ch_z = float(data.data[0])  # Channel Z
        ch_r = float(data.data[1])  # Channel R
        ch_l = float(data.data[2])  # Channel L
        battery = float(data.batlevel)
        
        print(f"ChZ: {ch_z:.2f}, ChR: {ch_r:.2f}, ChL: {ch_l:.2f}, Bat: {battery:.2f}")
        
        # Process your data here...
        break  # Remove this to continuously receive data
```

### Scan for Available Devices

```python
from pitaeeg import Sensor

with Sensor(port="COM3") as sensor:
    devices = sensor.scan_devices(timeout=10.0)
    for device in devices:
        print(f"Found: {device['name']} (ID: {device['id']})")
```

### Save Data to CSV

See the complete example in `examples/wireless_acquisition.py`:

```bash
python examples/wireless_acquisition.py COM3 HARU2-001 --out output.csv
```

Or run it directly:

```bash
./examples/wireless_acquisition.py COM3 HARU2-001
```

### API Reference

#### Sensor Class

**Constructor:**

- `Sensor(port, library_path=None, com_timeout=2000, scan_timeout=5000)`

**Methods:**

- `scan_devices(timeout=10.0)` - Scan for available devices
- `connect(device_name, scan_timeout=10.0)` - Connect to a specific device
- `start_measurement(enabled_channels=None)` - Start data acquisition
- `receive_data()` - Generator that yields received data
- `stop_measurement()` - Stop data acquisition
- `disconnect()` - Disconnect from device
- `close()` - Close sensor interface

**Properties:**

- `is_connected` - Check if device is connected
- `is_measuring` - Check if measurement is active

#### Exceptions

All exceptions inherit from `PitaEEGSensorError`:

- `LibraryNotFoundError` - Native library not found
- `InitializationError` - Sensor initialization failed
- `ScanError` - Device scanning failed
- `SensorConnectionError` - Device connection failed
- `MeasurementError` - Measurement operation failed

## Development

### Setup

Install pre-commit hooks for automatic code formatting and linting:

```bash
make precommit-install
```

### Code Quality

Run linters and formatters:

```bash
make check
```

This will run:

- `ruff` - Fast Python linter
- `ruff-format` - Code formatter
- `mypy` - Static type checker
- Various pre-commit hooks

### Testing

Run all tests:

```bash
make pytest
```

Run tests in parallel:

```bash
make pytest-dist
```

Generate coverage report:

```bash
make coverage
```

Generate coverage report in parallel:

```bash
make coverage-dist
```
