"""Data types and structures for PitaEEG sensor API."""

from __future__ import annotations

import ctypes
from typing import Any, ClassVar

MAX_CH = 8
"""Maximum number of EEG channels supported."""

HARU2_CH_NUM = 3
"""Number of EEG channels for HARU2 sensor model."""

MAX_DEVICENAME_LEN = 24
"""Maximum length of device name in bytes."""

MAX_DEVICEADDR_LEN = 8
"""Maximum length of device address in bytes."""


class TimesetParam(ctypes.Structure):
    """Timeout parameters for communication and scanning.

    Attributes:
        com_timeout (int): Communication timeout in milliseconds.
        scan_timeout (int): Device scanning timeout in milliseconds.

    """

    _fields_: ClassVar = [("com_timeout", ctypes.c_int), ("scan_timeout", ctypes.c_int)]


class DeviceInfo(ctypes.Structure):
    """Device information structure.

    Contains identifying information for a PitaEEG sensor device.

    Attributes:
        deviceid (bytes): Device ID as an array of bytes (8 bytes).
        devicename (bytes): Device name as a null-terminated string (24 bytes max).

    """

    _fields_: ClassVar = [
        ("deviceid", ctypes.c_ubyte * MAX_DEVICEADDR_LEN),
        ("devicename", ctypes.c_char * MAX_DEVICENAME_LEN),
    ]


class ReceiveData2(ctypes.Structure):
    """Received data structure for HARU2 sensor.

    Contains EEG measurement data received from the sensor device.

    Attributes:
        data (list[float]): Array of EEG channel data values (3 channels for HARU2).
            Each value represents the measured voltage in microvolts.
        batlevel (float): Battery level percentage (0.0 to 100.0).
        isRepair (int): Repair flag indicating data correction status (0 or 1).

    """

    _fields_: ClassVar = [
        ("data", ctypes.c_double * HARU2_CH_NUM),
        ("batlevel", ctypes.c_double),
        ("isRepair", ctypes.c_ubyte),
    ]


class SensorParam(ctypes.Structure):
    """Sensor parameter structure.

    Contains configuration parameters for sensor measurement channels.

    Attributes:
        usech (bytes): Array indicating which channels to use (8 bytes).
            Each byte represents a channel usage flag (0 = unused, 1 = used).
        reserve (bytes): Reserved field for future use (32 bytes).

    """

    _fields_: ClassVar = [
        ("usech", ctypes.c_ubyte * MAX_CH),
        ("reserve", ctypes.c_ubyte * 32),
    ]


class ContactResistance(ctypes.Structure):
    """Contact resistance values for each EEG channel.

    Contains the electrical contact resistance measurements for each electrode.
    Lower resistance values indicate better electrode contact with the skin.

    Attributes:
        ChZ (float): Contact resistance for the Z channel (ground/reference)
            in ohms (Ω).
        ChR (float): Contact resistance for the R channel (right hemisphere)
            in ohms (Ω).
        ChL (float): Contact resistance for the L channel (left hemisphere)
            in ohms (Ω).

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("ChZ", ctypes.c_float),
        ("ChR", ctypes.c_float),
        ("ChL", ctypes.c_float),
    ]
