"""Custom exceptions for PitaEEG sensor API."""


class PitaEEGSensorError(Exception):
    """Base exception for PitaEEG sensor API."""


class LibraryNotFoundError(PitaEEGSensorError):
    """Raised when the native library cannot be found or loaded."""


class InitializationError(PitaEEGSensorError):
    """Raised when sensor initialization fails."""


class ScanError(PitaEEGSensorError):
    """Raised when device scanning fails."""


class SensorConnectionError(PitaEEGSensorError):
    """Raised when device connection fails."""


class MeasurementError(PitaEEGSensorError):
    """Raised when measurement operation fails."""
