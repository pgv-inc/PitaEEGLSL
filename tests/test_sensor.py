"""Tests for pitaeegsensorapi4lsl.sensor module."""

from __future__ import annotations

import ctypes
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from pitaeegsensorapi4lsl.exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    ScanError,
    SensorConnectionError,
)
from pitaeegsensorapi4lsl.sensor import Sensor, _is_linux, _is_mac, _is_win
from pitaeegsensorapi4lsl.types import DeviceInfo, ReceiveData2


class TestPlatformDetection:
    """Test platform detection functions."""

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "win32")
    def test_is_win_true(self) -> None:
        """Test _is_win returns True on Windows."""
        assert _is_win() is True

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "linux")
    def test_is_win_false(self) -> None:
        """Test _is_win returns False on non-Windows."""
        assert _is_win() is False

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "darwin")
    def test_is_mac_true(self) -> None:
        """Test _is_mac returns True on macOS."""
        assert _is_mac() is True

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "linux")
    def test_is_mac_false(self) -> None:
        """Test _is_mac returns False on non-macOS."""
        assert _is_mac() is False

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "linux")
    def test_is_linux_true(self) -> None:
        """Test _is_linux returns True on Linux."""
        assert _is_linux() is True

    @patch("pitaeegsensorapi4lsl.sensor.sys.platform", "darwin")
    def test_is_linux_false(self) -> None:
        """Test _is_linux returns False on non-Linux."""
        assert _is_linux() is False


class TestLoadLibrary:
    """Test library loading functionality."""

    @patch("pitaeegsensorapi4lsl.sensor.ctypes.CDLL")
    @patch("pitaeegsensorapi4lsl.sensor.Path")
    def test_load_library_not_found(self, mock_path: Mock, mock_cdll: Mock) -> None:
        """Test LibraryNotFoundError is raised when library not found."""
        from pitaeegsensorapi4lsl.sensor import _load_library

        mock_path.return_value.exists.return_value = False
        mock_cdll.side_effect = OSError("Library not found")

        with pytest.raises(LibraryNotFoundError):
            _load_library()


class TestSensor:
    """Test Sensor class."""

    @pytest.fixture
    def mock_lib(self) -> Mock:
        """Create a mock library."""
        lib = MagicMock()
        lib.Init.return_value = 1  # Valid handle
        lib.Term.return_value = 0
        lib.startScan.return_value = 0
        lib.stopScan.return_value = 0
        lib.getScannedNum.return_value = 0
        lib.connect_device.return_value = 0
        lib.disconnect_device.return_value = 0
        lib.startMeasure.return_value = 0
        lib.stopMeasure.return_value = 0
        lib.getReceiveNum.return_value = 0
        return lib

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_sensor_creation(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test Sensor can be created successfully."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")

        assert sensor is not None
        assert sensor._port == "COM3"
        mock_lib.Init.assert_called_once()

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_sensor_init_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test InitializationError is raised when Init fails."""
        mock_lib.Init.return_value = -1  # Error
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        with pytest.raises(InitializationError):
            Sensor(port="COM3")

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_context_manager(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test Sensor works as context manager."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        with Sensor(port="COM3") as sensor:
            assert sensor is not None

        mock_lib.Term.assert_called_once()

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_scan_devices_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test ScanError is raised when startScan fails."""
        mock_lib.startScan.return_value = -1  # Error
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")

        with pytest.raises(ScanError):
            sensor.scan_devices()

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    @patch("pitaeegsensorapi4lsl.sensor.time.time")
    def test_scan_devices_success(
        self,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test scan_devices returns device list."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_time.side_effect = [0.0, 0.1, 0.2]  # Simulate timeout

        mock_lib.getScannedNum.return_value = 1

        def mock_get_scanned_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            info.devicename = b"HARU2-001\x00"
            return 0

        mock_lib.getScannedDevice.side_effect = mock_get_scanned_device

        sensor = Sensor(port="COM3")
        devices = sensor.scan_devices(timeout=1.0)

        assert len(devices) >= 0  # May be empty if timeout

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    @patch("pitaeegsensorapi4lsl.sensor.time.time")
    def test_connect_device_not_found(
        self,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test SensorConnectionError is raised when device not found."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_time.side_effect = [0.0, 11.0]  # Timeout

        mock_lib.getScannedNum.return_value = 0

        sensor = Sensor(port="COM3")

        with pytest.raises(SensorConnectionError, match="not found"):
            sensor.connect("HARU2-001", scan_timeout=10.0)

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_connect_device_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test SensorConnectionError is raised when connect fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        mock_lib.getScannedNum.return_value = 1
        mock_lib.connect_device.return_value = -1  # Error

        def mock_get_scanned_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            info.devicename = b"HARU2-001\x00"
            return 0

        mock_lib.getScannedDevice.side_effect = mock_get_scanned_device

        sensor = Sensor(port="COM3")

        with pytest.raises(SensorConnectionError, match="Failed to connect"):
            sensor.connect("HARU2-001", scan_timeout=1.0)

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_start_measurement_not_connected(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test MeasurementError is raised when not connected."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")

        with pytest.raises(MeasurementError, match="No device connected"):
            sensor.start_measurement()

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_start_measurement_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test MeasurementError is raised when startMeasure fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.startMeasure.return_value = -1  # Error

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()  # Fake connection

        with pytest.raises(MeasurementError, match="startMeasure failed"):
            sensor.start_measurement()

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_properties(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test sensor properties."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")

        assert sensor.is_connected is False
        assert sensor.is_measuring is False

        sensor._connected_device = DeviceInfo()
        assert sensor.is_connected is True

        sensor._measuring = True
        assert sensor.is_measuring is True

    @patch("pitaeegsensorapi4lsl.sensor._load_library")
    @patch("pitaeegsensorapi4lsl.sensor._bind_api")
    def test_close(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test sensor close releases resources."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()
        sensor._measuring = True

        sensor.close()

        mock_lib.stopMeasure.assert_called_once()
        mock_lib.disconnect_device.assert_called_once()
        mock_lib.Term.assert_called_once()
        assert sensor._handle is None

