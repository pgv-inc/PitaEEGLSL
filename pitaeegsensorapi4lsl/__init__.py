"""PitaEEG Sensor API for Python."""

__version__ = "0.1.0"
__title__ = "pitaeegsensorapi4lsl"
__description__ = "Python API for PitaEEG wireless sensor"
__url__ = "https://github.com/kezure/pitaeegsensorapi4lsl"
__author__ = "kezure <3447723+kezure@users.noreply.github.com>"

from pitaeegsensorapi4lsl.exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    PitaEEGSensorError,
    ScanError,
    SensorConnectionError,
)
from pitaeegsensorapi4lsl.sensor import Sensor
from pitaeegsensorapi4lsl.types import (
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
