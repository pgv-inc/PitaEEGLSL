"""Data types and structures for PitaEEG sensor API.

This module defines ctypes structures and constants used for communication
with the PitaEEG sensor native API library.
"""

from __future__ import annotations

import ctypes
from typing import Any, ClassVar

MAX_CH = 8
"""Maximum number of EEG channels supported (int)."""

HARU2_CH_NUM = 3
"""Number of EEG channels for HARU2 sensor model (int)."""

MAX_DEVICENAME_LEN = 24
"""Maximum length of device name in bytes (int)."""

MAX_DEVICEADDR_LEN = 8
"""Maximum length of device address in bytes (int)."""


class TimesetParam(ctypes.Structure):
    """Timeout parameters for communication and scanning.

    This structure is used to configure timeout values for serial communication
    and device scanning operations when initializing the sensor interface.

    Attributes:
        com_timeout (int): Communication timeout in milliseconds. Determines
            how long to wait for responses during serial communication.
        scan_timeout (int): Device scanning timeout in milliseconds. Determines
            how long to wait for devices to respond during scanning operations.

    """

    _fields_: ClassVar = [("com_timeout", ctypes.c_int), ("scan_timeout", ctypes.c_int)]


class DeviceInfo(ctypes.Structure):
    """Device information structure.

    Contains identifying information for a PitaEEG sensor device discovered
    during scanning operations. This structure is used internally for device
    connection and identification.

    Attributes:
        deviceid (bytes): Device ID as an array of bytes (8 bytes). Typically
            represented as a hexadecimal string when displayed to users.
        devicename (bytes): Device name as a null-terminated C string
            (24 bytes max). Contains the human-readable device name
            (e.g., "HARU2-001").

    """

    _fields_: ClassVar = [
        ("deviceid", ctypes.c_ubyte * MAX_DEVICEADDR_LEN),
        ("devicename", ctypes.c_char * MAX_DEVICENAME_LEN),
    ]


class ReceiveData2(ctypes.Structure):
    """Received data structure for HARU2 sensor.

    Contains EEG measurement data received from the sensor device during
    active measurement. This structure is yielded by the
    :meth:`Sensor.receive_data` generator.

    Attributes:
        data (list[float]): Array of EEG channel data values (3 channels for HARU2).
            Each value represents the measured voltage in microvolts (µV).
            The array length matches :const:`HARU2_CH_NUM`.
        batlevel (float): Battery level percentage ranging from 0.0 to 100.0.
            Indicates the current charge level of the sensor device.
        isRepair (int): Repair flag indicating data correction status.
            Value of 0 indicates normal data, 1 indicates that data correction
            algorithms were applied to compensate for signal quality issues.

    """

    _fields_: ClassVar = [
        ("data", ctypes.c_double * HARU2_CH_NUM),
        ("batlevel", ctypes.c_double),
        ("isRepair", ctypes.c_ubyte),
    ]


class SensorParam(ctypes.Structure):
    """Sensor parameter structure.

    Contains configuration parameters for sensor measurement channels.
    This structure is used to specify which EEG channels should be enabled
    during measurement operations.

    Attributes:
        usech (bytes): Array indicating which channels to use (8 bytes).
            Each byte represents a channel usage flag where 0 indicates the
            channel is unused and 1 indicates the channel is used.
            The array length matches :const:`MAX_CH`.
        reserve (bytes): Reserved field for future use (32 bytes).
            This field should be set to zero and is reserved for future
            API extensions.

    """

    _fields_: ClassVar = [
        ("usech", ctypes.c_ubyte * MAX_CH),
        ("reserve", ctypes.c_ubyte * 32),
    ]


class ContactResistance(ctypes.Structure):
    """Contact resistance values for each EEG channel.

    Contains the electrical contact resistance measurements for each electrode.
    Contact resistance is a measure of the electrical impedance between the
    electrode and the skin. Lower resistance values indicate better electrode
    contact with the skin, which generally leads to higher quality EEG signals.

    This structure is returned by :meth:`Sensor.get_contact_resistance` to
    provide real-time feedback on electrode contact quality.

    Attributes:
        ChZ (float): Contact resistance for the Z channel (ground/reference)
            in ohms (Ω). Lower values (typically < 10 kΩ) indicate good contact.
        ChR (float): Contact resistance for the R channel (right hemisphere)
            in ohms (Ω). Lower values (typically < 10 kΩ) indicate good contact.
        ChL (float): Contact resistance for the L channel (left hemisphere)
            in ohms (Ω). Lower values (typically < 10 kΩ) indicate good contact.

    Note:
        High resistance values (> 50 kΩ) may indicate poor electrode contact
        and can result in increased noise or signal artifacts in the EEG data.

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("ChZ", ctypes.c_float),
        ("ChR", ctypes.c_float),
        ("ChL", ctypes.c_float),
    ]
