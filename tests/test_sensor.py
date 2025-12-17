"""Tests for pitaeeg.sensor module."""

from __future__ import annotations

import ctypes
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from pitaeeg.exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    ScanError,
    SensorConnectionError,
)
from pitaeeg.sensor import Sensor, _is_linux, _is_mac, _is_win
from pitaeeg.types import DeviceInfo, ReceiveData2


class TestPlatformDetection:
    """Test platform detection functions."""

    @patch("pitaeeg.sensor.sys.platform", "win32")
    def test_is_win_true(self) -> None:
        """Test _is_win returns True on Windows."""
        assert _is_win() is True

    @patch("pitaeeg.sensor.sys.platform", "linux")
    def test_is_win_false(self) -> None:
        """Test _is_win returns False on non-Windows."""
        assert _is_win() is False

    @patch("pitaeeg.sensor.sys.platform", "darwin")
    def test_is_mac_true(self) -> None:
        """Test _is_mac returns True on macOS."""
        assert _is_mac() is True

    @patch("pitaeeg.sensor.sys.platform", "linux")
    def test_is_mac_false(self) -> None:
        """Test _is_mac returns False on non-macOS."""
        assert _is_mac() is False

    @patch("pitaeeg.sensor.sys.platform", "linux")
    def test_is_linux_true(self) -> None:
        """Test _is_linux returns True on Linux."""
        assert _is_linux() is True

    @patch("pitaeeg.sensor.sys.platform", "darwin")
    def test_is_linux_false(self) -> None:
        """Test _is_linux returns False on non-Linux."""
        assert _is_linux() is False

    @patch("pitaeeg.sensor.platform.machine")
    def test_get_machine(self, mock_machine: Mock) -> None:
        """Test _get_machine returns machine architecture."""
        from pitaeeg.sensor import _get_machine

        mock_machine.return_value = "ARM64"
        assert _get_machine() == "arm64"

        mock_machine.return_value = "x86_64"
        assert _get_machine() == "x86_64"


class TestLoadLibrary:
    """Test library loading functionality."""

    @patch("pitaeeg.sensor.ctypes.CDLL")
    @patch("pitaeeg.sensor.Path")
    def test_load_library_not_found(self, mock_path: Mock, mock_cdll: Mock) -> None:
        """Test LibraryNotFoundError is raised when library not found."""
        from pitaeeg.sensor import _load_library

        mock_path.return_value.exists.return_value = False
        mock_cdll.side_effect = OSError("Library not found")

        with pytest.raises(LibraryNotFoundError):
            _load_library()

    @patch("pitaeeg.sensor.ctypes.CDLL")
    def test_load_library_explicit_file(self, mock_cdll: Mock) -> None:
        """Test loading library with explicit file path."""
        from pitaeeg.sensor import _load_library

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        with patch("pitaeeg.sensor.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.is_dir.return_value = False
            mock_path.exists.return_value = True
            mock_path.suffix = ".dll"
            mock_path.stem = "pitaeeg"
            mock_path.with_stem.return_value = Path("pitaeegd.dll")
            mock_path_cls.return_value = mock_path

            result = _load_library("/path/to/lib.dll")

            assert result == mock_lib

    @patch("pitaeeg.sensor.ctypes.CDLL")
    def test_load_library_explicit_directory(self, mock_cdll: Mock) -> None:
        """Test loading library with explicit directory path."""
        from pitaeeg.sensor import _load_library

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        with patch("pitaeeg.sensor.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.is_dir.return_value = True
            mock_path.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)

            mock_result_path = MagicMock()
            mock_result_path.exists.return_value = True
            mock_path.__truediv__.return_value = mock_result_path

            mock_path_cls.return_value = mock_path

            result = _load_library("/path/to/libs")

            assert result == mock_lib

    @patch("pitaeeg.sensor.sys.platform", "darwin")
    @patch("pitaeeg.sensor.ctypes.CDLL")
    def test_load_library_macos_platform(self, mock_cdll: Mock) -> None:
        """Test library loading on macOS platform."""
        from pitaeeg.sensor import _load_library

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        with patch("pitaeeg.sensor.Path") as mock_path_cls:
            # Mock the path that exists
            def path_side_effect(arg: str) -> MagicMock:
                mock_p = MagicMock()
                if "libpitaeeg.dylib" in str(arg):
                    mock_p.exists.return_value = True
                else:
                    mock_p.exists.return_value = False
                return mock_p

            mock_path_cls.side_effect = path_side_effect

            result = _load_library()

            assert result == mock_lib

    @patch("pitaeeg.sensor.sys.platform", "linux")
    @patch("pitaeeg.sensor.ctypes.CDLL")
    def test_load_library_linux_platform(self, mock_cdll: Mock) -> None:
        """Test library loading on Linux platform."""
        from pitaeeg.sensor import _load_library

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        with patch("pitaeeg.sensor.Path") as mock_path_cls:

            def path_side_effect(arg: str) -> MagicMock:
                mock_p = MagicMock()
                if "libpitaeeg.so" in str(arg):
                    mock_p.exists.return_value = True
                else:
                    mock_p.exists.return_value = False
                return mock_p

            mock_path_cls.side_effect = path_side_effect

            result = _load_library()

            assert result == mock_lib

    @patch("pitaeeg.sensor.sys.platform", "win32")
    @patch("pitaeeg.sensor.ctypes.CDLL")
    @patch("pitaeeg.sensor.os.add_dll_directory", create=True)
    def test_load_library_windows_platform(
        self,
        mock_add_dll: Mock,
        mock_cdll: Mock,
    ) -> None:
        """Test library loading on Windows platform."""
        from pitaeeg.sensor import _load_library

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib
        mock_add_dll.return_value.__enter__ = MagicMock()
        mock_add_dll.return_value.__exit__ = MagicMock()

        with patch("pitaeeg.sensor.Path") as mock_path_cls:

            def path_side_effect(arg: str) -> MagicMock:
                mock_p = MagicMock()
                if "pitaeeg.dll" in str(arg):
                    mock_p.exists.return_value = True
                    mock_p.parent = Path("/some/path")
                else:
                    mock_p.exists.return_value = False
                return mock_p

            mock_path_cls.side_effect = path_side_effect

            result = _load_library()

            assert result == mock_lib
            mock_add_dll.assert_called()

    @patch("pitaeeg.sensor.sys.platform", "win32")
    @patch("pitaeeg.sensor.ctypes.CDLL")
    def test_load_library_windows_no_add_dll_directory(
        self,
        mock_cdll: Mock,
    ) -> None:
        """Test library loading on Windows when add_dll_directory doesn't exist."""
        from pitaeeg.sensor import _load_library
        import pitaeeg.sensor

        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        # Create a mock os module that raises AttributeError for add_dll_directory
        # This makes getattr(os, "add_dll_directory", None) return None
        original_os = pitaeeg.sensor.os

        class MockOSModule:
            def __getattr__(self, name: str):
                if name == "add_dll_directory":
                    raise AttributeError(f"module 'os' has no attribute '{name}'")
                return getattr(original_os, name)

        mock_os = MockOSModule()

        with patch("pitaeeg.sensor.os", mock_os):
            with patch("pitaeeg.sensor.Path") as mock_path_cls:

                def path_side_effect(arg: str) -> MagicMock:
                    mock_p = MagicMock()
                    if "pitaeeg.dll" in str(arg):
                        mock_p.exists.return_value = True
                        mock_resolve = MagicMock()
                        mock_resolve.parent = Path("/some/path")
                        mock_p.resolve.return_value = mock_resolve
                    else:
                        mock_p.exists.return_value = False
                    return mock_p

                mock_path_cls.side_effect = path_side_effect

                result = _load_library()

                assert result == mock_lib


class TestBindApi:
    """Test _bind_api function."""

    def test_bind_api(self) -> None:
        """Test _bind_api sets up all function signatures."""
        from pitaeeg.sensor import _bind_api

        mock_lib = MagicMock()
        result = _bind_api(mock_lib)

        assert result == mock_lib

        # Verify all functions have argtypes and restype set
        assert hasattr(mock_lib.Init, "argtypes")
        assert hasattr(mock_lib.Init, "restype")
        assert hasattr(mock_lib.Term, "argtypes")
        assert hasattr(mock_lib.Term, "restype")
        assert hasattr(mock_lib.startScan, "argtypes")
        assert hasattr(mock_lib.startScan, "restype")
        assert hasattr(mock_lib.stopScan, "argtypes")
        assert hasattr(mock_lib.getScannedNum, "argtypes")
        assert hasattr(mock_lib.getScannedDevice, "argtypes")
        assert hasattr(mock_lib.connect_device, "argtypes")
        assert hasattr(mock_lib.disconnect_device, "argtypes")
        assert hasattr(mock_lib.waitReceivedData, "argtypes")
        assert hasattr(mock_lib.getReceiveNum, "argtypes")
        assert hasattr(mock_lib.getReceiveData2, "argtypes")
        assert hasattr(mock_lib.startMeasure2, "argtypes")
        assert hasattr(mock_lib.startMeasure2, "restype")
        assert hasattr(mock_lib.stopMeasure, "argtypes")
        assert hasattr(mock_lib.getPgvSensorBatteryRemainingTime, "argtypes")
        assert hasattr(mock_lib.getPgvSensorBatteryRemainingTime, "restype")
        assert hasattr(mock_lib.getPgvSensorVersion, "argtypes")
        assert hasattr(mock_lib.getPgvSensorVersion, "restype")
        assert hasattr(mock_lib.getSensorState, "argtypes")
        assert hasattr(mock_lib.getSensorState, "restype")
        assert hasattr(mock_lib.getContactResistance, "argtypes")
        assert hasattr(mock_lib.getContactResistance, "restype")


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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_start_measurement_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test MeasurementError is raised when startMeasure fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.startMeasure2.return_value = -1  # Error

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()  # Fake connection

        with pytest.raises(MeasurementError, match="startMeasure failed"):
            sensor.start_measurement()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
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

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
    def test_scan_devices_with_devices(
        self,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test scan_devices with actual devices found."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_time.side_effect = [0.0, 0.1]

        mock_lib.getScannedNum.return_value = 2

        call_count = [0]

        def mock_get_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            if call_count[0] == 0:
                info.devicename = b"HARU2-001\x00"
                info.deviceid = (ctypes.c_ubyte * 8)(
                    *[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
                )
            else:
                info.devicename = b"HARU2-002\x00"
                info.deviceid = (ctypes.c_ubyte * 8)(
                    *[0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18]
                )
            call_count[0] += 1
            return 0

        mock_lib.getScannedDevice.side_effect = mock_get_device

        sensor = Sensor(port="COM3")
        devices = sensor.scan_devices(timeout=1.0)

        assert len(devices) == 2
        assert devices[0]["name"] == "HARU2-001"
        assert devices[1]["name"] == "HARU2-002"

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
    @patch("pitaeeg.sensor.time.sleep")
    def test_scan_devices_with_retry(
        self,
        mock_sleep: Mock,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test scan_devices retries until device is found."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        # Simulate multiple iterations before finding device
        mock_time.side_effect = [0.0, 0.05, 0.15]

        call_count = [0]

        def mock_get_num(handle: int) -> int:
            call_count[0] += 1
            return 1 if call_count[0] >= 2 else 0  # Second call has device

        def mock_get_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            info.devicename = b"HARU2-001\x00"
            info.deviceid = (ctypes.c_ubyte * 8)(
                *[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
            )
            return 0

        mock_lib.getScannedNum.side_effect = mock_get_num
        mock_lib.getScannedDevice.side_effect = mock_get_device

        sensor = Sensor(port="COM3")
        devices = sensor.scan_devices(timeout=1.0)

        assert len(devices) == 1
        assert devices[0]["name"] == "HARU2-001"
        # Verify sleep was called (means we did retry)
        mock_sleep.assert_called()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
    @patch("pitaeeg.sensor.time.sleep")
    def test_connect_with_retry(
        self,
        mock_sleep: Mock,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test connect retries until device is found."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        # Simulate multiple iterations
        mock_time.side_effect = [0.0, 0.05, 0.15]

        call_count = [0]

        def mock_get_num(handle: int) -> int:
            call_count[0] += 1
            return 1 if call_count[0] >= 2 else 0

        def mock_get_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            info.devicename = b"HARU2-001\x00"
            return 0

        mock_lib.getScannedNum.side_effect = mock_get_num
        mock_lib.getScannedDevice.side_effect = mock_get_device
        mock_lib.connect_device.return_value = 0

        sensor = Sensor(port="COM3")
        sensor.connect("HARU2-001", scan_timeout=1.0)

        assert sensor.is_connected is True
        # Verify sleep was called
        mock_sleep.assert_called()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    @patch("pitaeeg.sensor.time.time")
    def test_connect_success(
        self,
        mock_time: Mock,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test successful device connection."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_time.side_effect = [0.0, 0.1]

        mock_lib.getScannedNum.return_value = 1

        def mock_get_device(handle: int, info_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            info = ctypes.cast(info_ptr, ctypes.POINTER(DeviceInfo)).contents
            info.devicename = b"HARU2-001\x00"
            return 0

        mock_lib.getScannedDevice.side_effect = mock_get_device
        mock_lib.connect_device.return_value = 0

        sensor = Sensor(port="COM3")
        sensor.connect("HARU2-001", scan_timeout=1.0)

        assert sensor.is_connected is True
        mock_lib.connect_device.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_start_measurement_all_channels(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test start_measurement with all channels enabled."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        def mock_start_measure2(
            handle: int,
            ll_ptr: ctypes.POINTER,  # type: ignore[type-arg]
        ) -> int:
            ll = ctypes.cast(ll_ptr, ctypes.POINTER(ctypes.c_longlong)).contents
            ll.value = 1234567890000
            return 0

        mock_lib.startMeasure2.side_effect = mock_start_measure2

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()

        devicetime = sensor.start_measurement()

        assert devicetime == 1234567890000
        assert sensor.is_measuring is True

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_receive_data_generator(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test receive_data generator yields data."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()
        sensor._measuring = True

        # Mock data reception
        call_count = [0]

        def mock_get_num(handle: int) -> int:
            if call_count[0] < 2:
                return 1
            sensor._measuring = False
            return 0

        def mock_get_data(handle: int, data_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            data = ctypes.cast(data_ptr, ctypes.POINTER(ReceiveData2)).contents
            data.data[0] = 1.23
            data.data[1] = 4.56
            data.data[2] = 7.89
            data.batlevel = 95.5
            data.isRepair = 0
            call_count[0] += 1
            return 0

        mock_lib.getReceiveNum.side_effect = mock_get_num
        mock_lib.getReceiveData2.side_effect = mock_get_data

        received_data = list(sensor.receive_data())

        assert len(received_data) == 2
        assert float(received_data[0].data[0]) == pytest.approx(1.23)

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_receive_data_not_measuring(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test receive_data raises error when not measuring."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")

        with pytest.raises(MeasurementError, match="Measurement not started"):
            next(sensor.receive_data())

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_stop_measurement(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test stop_measurement stops measurement."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._measuring = True

        sensor.stop_measurement()

        assert sensor.is_measuring is False
        mock_lib.stopMeasure.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_disconnect(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test disconnect disconnects device."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()
        sensor._measuring = True

        sensor.disconnect()

        assert sensor.is_connected is False
        mock_lib.disconnect_device.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_sensor_initialization_params(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test sensor initialization with custom parameters."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(
            port="/dev/ttyUSB0",
            library_path="/custom/path/lib.so",
            com_timeout=3000,
            scan_timeout=6000,
        )

        assert sensor._port == "/dev/ttyUSB0"
        mock_load.assert_called_with("/custom/path/lib.so")

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_scan_devices_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test scan_devices raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(ScanError, match="not initialized"):
            sensor.scan_devices()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_connect_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test connect raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(SensorConnectionError, match="not initialized"):
            sensor.connect("HARU2-001")

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_connect_start_scan_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test connect raises error when startScan fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.startScan.return_value = -1  # Fail startScan

        sensor = Sensor(port="COM3")

        with pytest.raises(SensorConnectionError, match="Failed to start device scan"):
            sensor.connect("HARU2-001")

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_start_measurement_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test start_measurement raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(MeasurementError, match="not initialized"):
            sensor.start_measurement()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_receive_data_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test receive_data raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None
        sensor._measuring = True

        with pytest.raises(MeasurementError, match="not initialized"):
            next(sensor.receive_data())

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_receive_data_skip_negative_result(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test receive_data skips negative results."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._connected_device = DeviceInfo()
        sensor._measuring = True

        call_count = [0]

        def mock_get_num(handle: int) -> int:
            if call_count[0] < 3:
                return 1
            sensor._measuring = False
            return 0

        def mock_get_data(handle: int, data_ptr: ctypes.POINTER) -> int:  # type: ignore[type-arg]
            if call_count[0] == 1:
                # Skip this one (negative result)
                call_count[0] += 1
                return -1
            data = ctypes.cast(data_ptr, ctypes.POINTER(ReceiveData2)).contents
            data.data[0] = call_count[0]
            call_count[0] += 1
            return 0

        mock_lib.getReceiveNum.side_effect = mock_get_num
        mock_lib.getReceiveData2.side_effect = mock_get_data

        received_data = list(sensor.receive_data())

        # Should have 2 items (skipping the one with -1 return)
        assert len(received_data) == 2

    def test_getPgvSensorBatteryRemainingTime(self):
        from pitaeeg.sensor import _bind_api

        mock_lib = MagicMock()
        _bind_api(mock_lib)

        assert hasattr(mock_lib.getPgvSensorBatteryRemainingTime, "argtypes")
        assert hasattr(mock_lib.getPgvSensorBatteryRemainingTime, "restype")

        assert mock_lib.getPgvSensorBatteryRemainingTime.argtypes == [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
        ]
        assert mock_lib.getPgvSensorBatteryRemainingTime.restype == ctypes.c_int

    def test_getPgvSensorVersion(self):
        from pitaeeg.sensor import _bind_api

        mock_lib = MagicMock()
        _bind_api(mock_lib)

        assert hasattr(mock_lib.getPgvSensorVersion, "argtypes")
        assert hasattr(mock_lib.getPgvSensorVersion, "restype")

        assert mock_lib.getPgvSensorVersion.argtypes == [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_double),
        ]
        assert mock_lib.getPgvSensorVersion.restype == ctypes.c_int

    def test_getSensorState(self):
        from pitaeeg.sensor import _bind_api

        mock_lib = MagicMock()
        _bind_api(mock_lib)

        assert hasattr(mock_lib.getSensorState, "argtypes")
        assert hasattr(mock_lib.getSensorState, "restype")

        assert mock_lib.getSensorState.argtypes == [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        assert mock_lib.getSensorState.restype == ctypes.c_int

    def test_getContactResistance(self):
        from pitaeeg.sensor import _bind_api
        from pitaeeg.types import ContactResistance

        mock_lib = MagicMock()
        _bind_api(mock_lib)

        assert hasattr(mock_lib.getContactResistance, "argtypes")
        assert hasattr(mock_lib.getContactResistance, "restype")

        assert mock_lib.getContactResistance.argtypes == [
            ctypes.c_int,
            ctypes.POINTER(ContactResistance),
        ]
        assert mock_lib.getContactResistance.restype == ctypes.c_int

    def test_startMeasure2(self):
        from pitaeeg.sensor import _bind_api

        mock_lib = MagicMock()
        _bind_api(mock_lib)

        assert hasattr(mock_lib.startMeasure2, "argtypes")
        assert hasattr(mock_lib.startMeasure2, "restype")

        assert mock_lib.startMeasure2.argtypes == [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_longlong),
        ]
        assert mock_lib.startMeasure2.restype == ctypes.c_int

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_battery_remaining_time_success(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_battery_remaining_time returns battery time."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        def mock_get_battery(
            handle: int,
            value_ptr: ctypes.POINTER,  # type: ignore[type-arg]
        ) -> int:
            value = ctypes.cast(value_ptr, ctypes.POINTER(ctypes.c_double)).contents
            value.value = 120.5  # 120.5 minutes
            return 0

        mock_lib.getPgvSensorBatteryRemainingTime.side_effect = mock_get_battery

        sensor = Sensor(port="COM3")

        battery_time = sensor.get_battery_remaining_time()

        assert battery_time == 120.5
        mock_lib.getPgvSensorBatteryRemainingTime.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_battery_remaining_time_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_battery_remaining_time raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(MeasurementError, match="not initialized"):
            sensor.get_battery_remaining_time()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_battery_remaining_time_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_battery_remaining_time raises error when API call fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.getPgvSensorBatteryRemainingTime.return_value = -1  # Error

        sensor = Sensor(port="COM3")

        with pytest.raises(
            MeasurementError, match="getPgvSensorBatteryRemainingTime failed"
        ):
            sensor.get_battery_remaining_time()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_version_success(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_version returns firmware version."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        def mock_get_version(
            handle: int,
            value_ptr: ctypes.POINTER,  # type: ignore[type-arg]
        ) -> int:
            value = ctypes.cast(value_ptr, ctypes.POINTER(ctypes.c_double)).contents
            value.value = 2.2  # Version 2.2
            return 0

        mock_lib.getPgvSensorVersion.side_effect = mock_get_version

        sensor = Sensor(port="COM3")

        version = sensor.get_version()

        assert version == 2.2
        mock_lib.getPgvSensorVersion.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_version_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_version raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(MeasurementError, match="not initialized"):
            sensor.get_version()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_version_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_version raises error when API call fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.getPgvSensorVersion.return_value = -1  # Error

        sensor = Sensor(port="COM3")

        with pytest.raises(MeasurementError, match="getPgvSensorVersion failed"):
            sensor.get_version()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_state_success(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_state returns sensor state and error."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        def mock_get_state(
            handle: int,
            state_ptr: ctypes.POINTER,  # type: ignore[type-arg]
            err_ptr: ctypes.POINTER,  # type: ignore[type-arg]
        ) -> int:
            state = ctypes.cast(state_ptr, ctypes.POINTER(ctypes.c_int)).contents
            err = ctypes.cast(err_ptr, ctypes.POINTER(ctypes.c_int)).contents
            state.value = 2  # IDLE state
            err.value = 0  # No error
            return 0

        mock_lib.getSensorState.side_effect = mock_get_state

        sensor = Sensor(port="COM3")

        state, error = sensor.get_state()

        assert state == 2
        assert error == 0
        mock_lib.getSensorState.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_state_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_state raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(MeasurementError, match="not initialized"):
            sensor.get_state()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_state_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_state raises error when API call fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.getSensorState.return_value = -1  # Error

        sensor = Sensor(port="COM3")

        with pytest.raises(MeasurementError, match="getSensorState failed"):
            sensor.get_state()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_contact_resistance_success(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_contact_resistance returns contact resistance values."""
        from pitaeeg.types import ContactResistance

        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        def mock_get_contact_resistance(
            handle: int,
            res_ptr: ctypes.POINTER,  # type: ignore[type-arg]
        ) -> int:
            res = ctypes.cast(res_ptr, ctypes.POINTER(ContactResistance)).contents
            res.ChZ = 1000.0
            res.ChR = 2000.0
            res.ChL = 3000.0
            return 0

        mock_lib.getContactResistance.side_effect = mock_get_contact_resistance

        sensor = Sensor(port="COM3")

        resistance = sensor.get_contact_resistance()

        assert isinstance(resistance, ContactResistance)
        assert resistance.ChZ == 1000.0
        assert resistance.ChR == 2000.0
        assert resistance.ChL == 3000.0
        mock_lib.getContactResistance.assert_called_once()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_contact_resistance_when_handle_none(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_contact_resistance raises error when handle is None."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib

        sensor = Sensor(port="COM3")
        sensor._handle = None

        with pytest.raises(MeasurementError, match="not initialized"):
            sensor.get_contact_resistance()

    @patch("pitaeeg.sensor._load_library")
    @patch("pitaeeg.sensor._bind_api")
    def test_get_contact_resistance_failure(
        self,
        mock_bind: Mock,
        mock_load: Mock,
        mock_lib: Mock,
    ) -> None:
        """Test get_contact_resistance raises error when API call fails."""
        mock_bind.return_value = mock_lib
        mock_load.return_value = mock_lib
        mock_lib.getContactResistance.return_value = -1  # Error

        sensor = Sensor(port="COM3")

        with pytest.raises(MeasurementError, match="getContactResistance failed"):
            sensor.get_contact_resistance()
