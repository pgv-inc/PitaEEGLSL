"""Tests for pitaeegsensorapi4lsl.exceptions module."""

from __future__ import annotations

import pytest

from pitaeegsensorapi4lsl.exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    PitaEEGSensorError,
    ScanError,
    SensorConnectionError,
)


class TestPitaEEGSensorError:
    """Test PitaEEGSensorError base exception."""

    def test_is_exception(self) -> None:
        """Test PitaEEGSensorError is an Exception."""
        assert issubclass(PitaEEGSensorError, Exception)

    def test_can_be_raised(self) -> None:
        """Test PitaEEGSensorError can be raised."""
        with pytest.raises(PitaEEGSensorError):
            raise PitaEEGSensorError("Test error")

    def test_error_message(self) -> None:
        """Test error message is preserved."""
        msg = "Test error message"
        with pytest.raises(PitaEEGSensorError, match=msg):
            raise PitaEEGSensorError(msg)


class TestLibraryNotFoundError:
    """Test LibraryNotFoundError exception."""

    def test_inherits_from_base(self) -> None:
        """Test LibraryNotFoundError inherits from PitaEEGSensorError."""
        assert issubclass(LibraryNotFoundError, PitaEEGSensorError)

    def test_can_be_raised(self) -> None:
        """Test LibraryNotFoundError can be raised."""
        with pytest.raises(LibraryNotFoundError):
            raise LibraryNotFoundError("Library not found")

    def test_caught_as_base_exception(self) -> None:
        """Test LibraryNotFoundError can be caught as PitaEEGSensorError."""
        with pytest.raises(PitaEEGSensorError):
            raise LibraryNotFoundError("Library not found")


class TestInitializationError:
    """Test InitializationError exception."""

    def test_inherits_from_base(self) -> None:
        """Test InitializationError inherits from PitaEEGSensorError."""
        assert issubclass(InitializationError, PitaEEGSensorError)

    def test_can_be_raised(self) -> None:
        """Test InitializationError can be raised."""
        with pytest.raises(InitializationError):
            raise InitializationError("Initialization failed")

    def test_caught_as_base_exception(self) -> None:
        """Test InitializationError can be caught as PitaEEGSensorError."""
        with pytest.raises(PitaEEGSensorError):
            raise InitializationError("Initialization failed")


class TestScanError:
    """Test ScanError exception."""

    def test_inherits_from_base(self) -> None:
        """Test ScanError inherits from PitaEEGSensorError."""
        assert issubclass(ScanError, PitaEEGSensorError)

    def test_can_be_raised(self) -> None:
        """Test ScanError can be raised."""
        with pytest.raises(ScanError):
            raise ScanError("Scan failed")

    def test_caught_as_base_exception(self) -> None:
        """Test ScanError can be caught as PitaEEGSensorError."""
        with pytest.raises(PitaEEGSensorError):
            raise ScanError("Scan failed")


class TestSensorConnectionError:
    """Test SensorConnectionError exception."""

    def test_inherits_from_base(self) -> None:
        """Test SensorConnectionError inherits from PitaEEGSensorError."""
        assert issubclass(SensorConnectionError, PitaEEGSensorError)

    def test_can_be_raised(self) -> None:
        """Test SensorConnectionError can be raised."""
        with pytest.raises(SensorConnectionError):
            raise SensorConnectionError("Connection failed")

    def test_caught_as_base_exception(self) -> None:
        """Test SensorConnectionError can be caught as PitaEEGSensorError."""
        with pytest.raises(PitaEEGSensorError):
            raise SensorConnectionError("Connection failed")


class TestMeasurementError:
    """Test MeasurementError exception."""

    def test_inherits_from_base(self) -> None:
        """Test MeasurementError inherits from PitaEEGSensorError."""
        assert issubclass(MeasurementError, PitaEEGSensorError)

    def test_can_be_raised(self) -> None:
        """Test MeasurementError can be raised."""
        with pytest.raises(MeasurementError):
            raise MeasurementError("Measurement failed")

    def test_caught_as_base_exception(self) -> None:
        """Test MeasurementError can be caught as PitaEEGSensorError."""
        with pytest.raises(PitaEEGSensorError):
            raise MeasurementError("Measurement failed")


class TestExceptionHierarchy:
    """Test exception hierarchy."""

    def test_all_inherit_from_base(self) -> None:
        """Test all custom exceptions inherit from PitaEEGSensorError."""
        exceptions = [
            LibraryNotFoundError,
            InitializationError,
            ScanError,
            SensorConnectionError,
            MeasurementError,
        ]

        for exc in exceptions:
            assert issubclass(exc, PitaEEGSensorError)

    def test_catch_all_with_base(self) -> None:
        """Test all exceptions can be caught with base exception."""
        exceptions = [
            LibraryNotFoundError("test"),
            InitializationError("test"),
            ScanError("test"),
            SensorConnectionError("test"),
            MeasurementError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(PitaEEGSensorError):
                raise exc
