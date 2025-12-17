"""Custom exceptions for PitaEEG sensor API."""


class PitaEEGSensorError(Exception):
    """Base exception for PitaEEG sensor API.

    All exceptions raised by the PitaEEG sensor library inherit from this
    base class. This allows catching all sensor-related errors with a single
    exception handler.
    """


class LibraryNotFoundError(PitaEEGSensorError):
    """Raised when the native library cannot be found or loaded.

    This exception is raised when the native C/C++ library required for
    sensor communication cannot be located in any of the search paths,
    or when loading the library fails due to platform-specific issues.
    """


class InitializationError(PitaEEGSensorError):
    """Raised when sensor initialization fails.

    This exception is raised during :meth:`Sensor.__init__` when the
    native API's Init function returns an error code, indicating that
    the sensor interface could not be properly initialized.
    """


class ScanError(PitaEEGSensorError):
    """Raised when device scanning fails.

    This exception is raised by :meth:`Sensor.scan_devices` when the
    scanning operation fails, such as when the startScan API call
    returns an error code.
    """


class SensorConnectionError(PitaEEGSensorError):
    """Raised when device connection fails.

    This exception is raised by :meth:`Sensor.connect` when:
    - The device scan fails
    - The specified device name cannot be found
    - The connect_device API call returns an error code
    """


class MeasurementError(PitaEEGSensorError):
    """Raised when measurement operation fails.

    This exception is raised by various measurement-related methods when:
    - The sensor is not initialized or connected
    - Starting/stopping measurement fails
    - Receiving data fails
    - Getting sensor status, battery, version, or contact resistance fails
    """
