"""Custom exceptions for PitaEEG sensor API.

This module defines exception classes used throughout the PitaEEG sensor library.
All exceptions inherit from :class:`PitaEEGSensorError`, allowing users to
catch all sensor-related errors with a single exception handler.
"""


class PitaEEGSensorError(Exception):
    """Base exception for PitaEEG sensor API.

    All exceptions raised by the PitaEEG sensor library inherit from this
    base class. This allows catching all sensor-related errors with a single
    exception handler.

    Example:
        >>> try:
        ...     sensor = Sensor(port="COM3")
        ...     sensor.connect("HARU2-001")
        ... except PitaEEGSensorError as e:
        ...     print(f"Sensor error: {e}")

    """


class LibraryNotFoundError(PitaEEGSensorError):
    """Raised when the native library cannot be found or loaded.

    This exception is raised when the native C/C++ library required for
    sensor communication cannot be located in any of the search paths,
    or when loading the library fails due to platform-specific issues.

    This typically occurs when:
    - The library file is not present in the expected locations
    - The library file is corrupted or incompatible with the current platform
    - Required system dependencies are missing
    """


class InitializationError(PitaEEGSensorError):
    """Raised when sensor initialization fails.

    This exception is raised during :meth:`Sensor.__init__` when the
    native API's Init function returns an error code, indicating that
    the sensor interface could not be properly initialized.

    Common causes include:
    - Invalid serial port name or port not accessible
    - Port already in use by another application
    - Hardware communication failure
    - Invalid timeout parameters
    """


class ScanError(PitaEEGSensorError):
    """Raised when device scanning fails.

    This exception is raised by :meth:`Sensor.scan_devices` when the
    scanning operation fails, such as when the startScan API call
    returns an error code.

    Common causes include:
    - Sensor not initialized
    - Communication failure with USB receiver
    - Hardware malfunction
    """


class SensorConnectionError(PitaEEGSensorError):
    """Raised when device connection fails.

    This exception is raised by :meth:`Sensor.connect` when:
    - The device scan fails
    - The specified device name cannot be found within the timeout period
    - The connect_device API call returns an error code

    Common causes include:
    - Device not powered on or out of range
    - Device name mismatch (check with :meth:`Sensor.scan_devices`)
    - Device already connected to another application
    - Communication timeout
    """


class MeasurementError(PitaEEGSensorError):
    """Raised when measurement operation fails.

    This exception is raised by various measurement-related methods when:
    - The sensor is not initialized or connected
    - Starting/stopping measurement fails
    - Receiving data fails
    - Getting sensor status, battery, version, or contact resistance fails

    Methods that may raise this exception:
    - :meth:`Sensor.start_measurement`
    - :meth:`Sensor.receive_data`
    - :meth:`Sensor.get_battery_remaining_time`
    - :meth:`Sensor.get_version`
    - :meth:`Sensor.get_state`
    - :meth:`Sensor.get_contact_resistance`
    """
