"""PitaEEG Sensor Library for Python.

This package provides a Python interface for communicating with PitaEEG
sensor devices. It enables device discovery, connection, measurement,
and data acquisition through a high-level API.

The main entry point is the :class:`Sensor` class, which manages the
connection to a sensor device and provides methods for scanning devices,
connecting, starting/stopping measurements, and receiving EEG data.

Example:
    Basic usage of the Sensor class::

        from pitaeeg import Sensor

        # Create and initialize sensor
        sensor = Sensor(port="COM3")

        # Scan for available devices
        devices = sensor.scan_devices(timeout=10.0)

        # Connect to a specific device
        sensor.connect("HARU2-001")

        # Start measurement
        device_time = sensor.start_measurement()

        # Receive data
        for data in sensor.receive_data():
            print(f"Channels: {data.data}, Battery: {data.batlevel}%")

        # Clean up
        sensor.stop_measurement()
        sensor.disconnect()
        sensor.close()

    Using as a context manager::

        with Sensor(port="COM3") as sensor:
            devices = sensor.scan_devices()
            sensor.connect("HARU2-001")
            sensor.start_measurement()
            for data in sensor.receive_data():
                process_data(data)

"""

__version__ = "0.15.0"
__title__ = "pitaeeg"
__description__ = "PitaEEG LSL(LabStreamingLayer) for Python"
__url__ = "https://github.com/pgv-inc/PitaEEGLSL"
__author__ = "kezure <3447723+kezure@users.noreply.github.com>"

from pitaeeg.exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    PitaEEGSensorError,
    ScanError,
    SensorConnectionError,
)
from pitaeeg.sensor import Sensor
from pitaeeg.types import (
    DeviceInfo,
    ReceiveData2,
    SensorParam,
    TimesetParam,
)

__all__ = [
    "DeviceInfo",
    "InitializationError",
    "LibraryNotFoundError",
    "MeasurementError",
    "PitaEEGSensorError",
    "ReceiveData2",
    "ScanError",
    "Sensor",
    "SensorConnectionError",
    "SensorParam",
    "TimesetParam",
]
