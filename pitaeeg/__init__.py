"""PitaEEG LSL for Python."""

__version__ = "0.1.2"
__title__ = "pitaeeg"
__description__ = "PitaEEG LSL for Python"
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
