"""Data types and structures for PitaEEG sensor API."""

from __future__ import annotations

import ctypes
from typing import ClassVar

MAX_CH = 8
HARU2_CH_NUM = 3
MAX_DEVICENAME_LEN = 24
MAX_DEVICEADDR_LEN = 8


class TimesetParam(ctypes.Structure):
    """Timeout parameters for communication and scanning."""

    _fields_: ClassVar = [("com_timeout", ctypes.c_int), ("scan_timeout", ctypes.c_int)]


class DeviceInfo(ctypes.Structure):
    """Device information structure."""

    _fields_: ClassVar = [
        ("deviceid", ctypes.c_ubyte * MAX_DEVICEADDR_LEN),
        ("devicename", ctypes.c_char * MAX_DEVICENAME_LEN),
    ]


class ReceiveData2(ctypes.Structure):
    """Received data structure for HARU2 sensor."""

    _fields_: ClassVar = [
        ("data", ctypes.c_double * HARU2_CH_NUM),
        ("batlevel", ctypes.c_double),
        ("isRepair", ctypes.c_ubyte),
    ]


class SensorParam(ctypes.Structure):
    """Sensor parameter structure."""

    _fields_: ClassVar = [
        ("usech", ctypes.c_ubyte * MAX_CH),
        ("reserve", ctypes.c_ubyte * 32),
    ]


class ContactResistance(ctypes.Structure):
    """Contact resistance values for each EEG channel."""

    _fields_: ClassVar[list[tuple[str, ctypes.c_float]]] = [
        ("ChZ", ctypes.c_float),
        ("ChR", ctypes.c_float),
        ("ChL", ctypes.c_float),
    ]
