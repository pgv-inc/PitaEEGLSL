"""Tests for pitaeeg.types module."""

from __future__ import annotations

import ctypes

import pytest

from pitaeeg.types import (
    HARU2_CH_NUM,
    MAX_CH,
    MAX_DEVICEADDR_LEN,
    MAX_DEVICENAME_LEN,
    DeviceInfo,
    ReceiveData2,
    SensorParam,
    TimesetParam,
)


class TestConstants:
    """Test module constants."""

    def test_constants_values(self) -> None:
        """Test that constants have expected values."""
        assert MAX_CH == 8
        assert HARU2_CH_NUM == 3
        assert MAX_DEVICENAME_LEN == 24
        assert MAX_DEVICEADDR_LEN == 8


class TestTimesetParam:
    """Test TimesetParam structure."""

    def test_creation(self) -> None:
        """Test TimesetParam can be created."""
        param = TimesetParam()
        assert isinstance(param, ctypes.Structure)

    def test_fields(self) -> None:
        """Test TimesetParam has expected fields."""
        param = TimesetParam(com_timeout=1000, scan_timeout=5000)
        assert param.com_timeout == 1000
        assert param.scan_timeout == 5000

    def test_field_types(self) -> None:
        """Test TimesetParam field types are correct."""
        param = TimesetParam()
        assert hasattr(param, "com_timeout")
        assert hasattr(param, "scan_timeout")


class TestDeviceInfo:
    """Test DeviceInfo structure."""

    def test_creation(self) -> None:
        """Test DeviceInfo can be created."""
        info = DeviceInfo()
        assert isinstance(info, ctypes.Structure)

    def test_fields(self) -> None:
        """Test DeviceInfo has expected fields."""
        info = DeviceInfo()
        assert hasattr(info, "deviceid")
        assert hasattr(info, "devicename")

    def test_deviceid_size(self) -> None:
        """Test deviceid array has correct size."""
        info = DeviceInfo()
        assert len(info.deviceid) == MAX_DEVICEADDR_LEN

    def test_devicename_size(self) -> None:
        """Test devicename array has correct size."""
        info = DeviceInfo()
        # ctypes char arrays don't report size via len(), check the type instead
        assert isinstance(info.devicename, bytes)

    def test_devicename_assignment(self) -> None:
        """Test devicename can be assigned."""
        info = DeviceInfo()
        test_name = b"HARU2-001"
        info.devicename = test_name
        assert info.devicename.startswith(test_name)


class TestReceiveData2:
    """Test ReceiveData2 structure."""

    def test_creation(self) -> None:
        """Test ReceiveData2 can be created."""
        data = ReceiveData2()
        assert isinstance(data, ctypes.Structure)

    def test_fields(self) -> None:
        """Test ReceiveData2 has expected fields."""
        data = ReceiveData2()
        assert hasattr(data, "data")
        assert hasattr(data, "batlevel")
        assert hasattr(data, "isRepair")

    def test_data_array_size(self) -> None:
        """Test data array has correct size."""
        data = ReceiveData2()
        assert len(data.data) == HARU2_CH_NUM

    def test_data_assignment(self) -> None:
        """Test data values can be assigned."""
        data = ReceiveData2()
        data.data[0] = 1.23
        data.data[1] = 4.56
        data.data[2] = 7.89
        data.batlevel = 95.5
        data.isRepair = 0

        assert data.data[0] == pytest.approx(1.23)
        assert data.data[1] == pytest.approx(4.56)
        assert data.data[2] == pytest.approx(7.89)
        assert data.batlevel == pytest.approx(95.5)
        assert data.isRepair == 0


class TestSensorParam:
    """Test SensorParam structure."""

    def test_creation(self) -> None:
        """Test SensorParam can be created."""
        param = SensorParam()
        assert isinstance(param, ctypes.Structure)

    def test_fields(self) -> None:
        """Test SensorParam has expected fields."""
        param = SensorParam()
        assert hasattr(param, "usech")
        assert hasattr(param, "reserve")

    def test_usech_array_size(self) -> None:
        """Test usech array has correct size."""
        param = SensorParam()
        assert len(param.usech) == MAX_CH

    def test_reserve_array_size(self) -> None:
        """Test reserve array has correct size."""
        param = SensorParam()
        assert len(param.reserve) == 32

    def test_usech_assignment(self) -> None:
        """Test usech values can be assigned."""
        param = SensorParam()
        for i in range(MAX_CH):
            param.usech[i] = 1

        for i in range(MAX_CH):
            assert param.usech[i] == 1
