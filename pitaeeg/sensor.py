"""Core sensor API for PitaEEG wireless sensor."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Self

from .exceptions import (
    InitializationError,
    LibraryNotFoundError,
    MeasurementError,
    ScanError,
    SensorConnectionError,
)
from .types import DeviceInfo, ReceiveData2, SensorParam, TimesetParam

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType


def _is_win() -> bool:
    return sys.platform.startswith("win")


def _is_mac() -> bool:
    return sys.platform.startswith("darwin")


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


def _get_machine() -> str:
    """Get machine architecture (arm64, x86_64, etc)."""
    return platform.machine().lower()


def _load_library(explicit_path: str | None = None) -> ctypes.CDLL:  # noqa: C901, PLR0912
    """Load the native library from the specified path or default locations.

    Args:
        explicit_path: Path to the library file or directory containing it.

    Returns:
        ctypes.CDLL: Loaded library handle.

    Raises:
        LibraryNotFoundError: If the library could not be found or loaded.

    """
    # If a directory is passed, search within it (try with 'd' suffix too)
    names = (
        ["pitaeegsensor.dll", "pitaeegsensord.dll"]
        if _is_win()
        else ["libpitaeegsensor.dylib", "libpitaeegsensord.dylib"]
        if _is_mac()
        else ["libpitaeegsensor.so", "libpitaeegsensord.so"]
    )

    here = Path(__file__).resolve().parent
    repo_root = here.parent
    libs_dir = repo_root / "libs"

    cand: list[Path] = []

    if explicit_path:
        p = Path(explicit_path)
        if p.is_dir():
            cand.extend(p / n for n in names)
        else:
            cand.append(p)
            if p.suffix and not p.stem.endswith("d"):
                cand.append(p.with_stem(p.stem + "d"))
    else:
        # Default search locations
        # 1. Check libs directory with platform-specific subdirectories
        if _is_mac():
            machine = _get_machine()
            platform_dir = libs_dir / "macos" / machine
            if platform_dir.exists():
                cand.extend(platform_dir / n for n in names)
            # Also try without machine subdirectory
            platform_dir = libs_dir / "macos"
            if platform_dir.exists():
                cand.extend(platform_dir / n for n in names)
        elif _is_linux():
            platform_dir = libs_dir / "linux"
            if platform_dir.exists():
                cand.extend(platform_dir / n for n in names)
        elif _is_win():
            platform_dir = libs_dir / "windows"
            if platform_dir.exists():
                cand.extend(platform_dir / n for n in names)

        # 2. Check current directory (pitaeeg package directory)
        cand.extend(here / n for n in names)

        # 3. Check working directory
        cand.extend(Path(n) for n in names)

    last = None
    for c in cand:
        if not c.exists():
            continue
        try:
            if _is_win():
                with os.add_dll_directory(str(c.parent)):  # type: ignore[attr-defined]
                    return ctypes.CDLL(str(c))
            return ctypes.CDLL(str(c))
        except OSError as e:
            last = e

    msg = f"Native lib not found. Tried: {[str(x) for x in cand]}. Last: {last}"
    raise LibraryNotFoundError(msg)


def _bind_api(lib: ctypes.CDLL) -> ctypes.CDLL:
    """Bind API function signatures to the loaded library.

    Args:
        lib: ctypes.CDLL library handle.

    Returns:
        ctypes.CDLL: The library with bound function signatures.

    """
    lib.Init.argtypes = [ctypes.c_char_p, ctypes.POINTER(TimesetParam)]
    lib.Init.restype = ctypes.c_int

    lib.Term.argtypes = [ctypes.c_int]
    lib.Term.restype = ctypes.c_int

    lib.startScan.argtypes = [ctypes.c_int]
    lib.startScan.restype = ctypes.c_int

    lib.stopScan.argtypes = [ctypes.c_int]
    lib.stopScan.restype = ctypes.c_int

    lib.getScannedNum.argtypes = [ctypes.c_int]
    lib.getScannedNum.restype = ctypes.c_int

    lib.getScannedDevice.argtypes = [ctypes.c_int, ctypes.POINTER(DeviceInfo)]
    lib.getScannedDevice.restype = ctypes.c_int

    lib.connect_device.argtypes = [ctypes.c_int, ctypes.POINTER(DeviceInfo)]
    lib.connect_device.restype = ctypes.c_int

    lib.disconnect_device.argtypes = [ctypes.c_int]
    lib.disconnect_device.restype = ctypes.c_int

    # Wait for and get received data count
    lib.waitReceivedData.argtypes = [ctypes.c_int]
    lib.waitReceivedData.restype = ctypes.c_int

    lib.getReceiveNum.argtypes = [ctypes.c_int]
    lib.getReceiveNum.restype = ctypes.c_int

    lib.getReceiveData2.argtypes = [ctypes.c_int, ctypes.POINTER(ReceiveData2)]
    lib.getReceiveData2.restype = ctypes.c_int

    # startMeasure: SENSOR_PARAM*, double*, long long*
    lib.startMeasure.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(SensorParam),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_longlong),
    ]
    lib.startMeasure.restype = ctypes.c_int

    lib.stopMeasure.argtypes = [ctypes.c_int]
    lib.stopMeasure.restype = ctypes.c_int
    return lib


class Sensor:
    """PitaEEG wireless sensor interface.

    Example:
        >>> sensor = Sensor(port="COM3", library_path="path/to/lib")
        >>> sensor.scan_devices(timeout=10)
        >>> sensor.connect("HARU2-001")
        >>> sensor.start_measurement()
        >>> for data in sensor.receive_data():
        ...     print(data)
        >>> sensor.stop_measurement()
        >>> sensor.disconnect()
        >>> sensor.close()

    """

    def __init__(
        self,
        port: str,
        library_path: str | None = None,
        com_timeout: int = 2000,
        scan_timeout: int = 5000,
    ) -> None:
        """Initialize the sensor interface.

        Args:
            port: Serial port name (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux).
            library_path: Optional path to the native library file or directory.
            com_timeout: Communication timeout in milliseconds (default: 2000).
            scan_timeout: Scan timeout in milliseconds (default: 5000).

        Raises:
            LibraryNotFoundError: If the native library cannot be found.
            InitializationError: If sensor initialization fails.

        """
        self._lib = _bind_api(_load_library(library_path))
        self._port = port
        self._handle: int | None = None
        self._connected_device: DeviceInfo | None = None
        self._measuring = False

        # Initialize
        timeout = TimesetParam(com_timeout=com_timeout, scan_timeout=scan_timeout)
        handle = self._lib.Init(port.encode("ascii"), ctypes.byref(timeout))
        if handle < 0:
            msg = f"Init failed with error code: {handle}"
            raise InitializationError(msg)
        self._handle = handle

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()

    def scan_devices(self, timeout: float = 10.0) -> list[dict[str, str]]:
        """Scan for available devices.

        Args:
            timeout: Scan timeout in seconds (default: 10.0).

        Returns:
            List of dictionaries containing device information.
            Each dictionary has 'name' and 'id' keys.

        Raises:
            ScanError: If scanning fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise ScanError(msg)

        if self._lib.startScan(self._handle) != 0:
            msg = "Failed to start device scan"
            raise ScanError(msg)

        devices = []
        t0 = time.time()

        try:
            while time.time() - t0 < timeout:
                n = self._lib.getScannedNum(self._handle)
                for _ in range(n):
                    info = DeviceInfo()
                    if (
                        self._lib.getScannedDevice(self._handle, ctypes.byref(info))
                        == 0
                    ):
                        name = (
                            bytes(info.devicename)
                            .split(b"\x00", 1)[0]
                            .decode(errors="ignore")
                        )
                        device_id = bytes(info.deviceid).hex()
                        devices.append({"name": name, "id": device_id})

                if devices:
                    break
                time.sleep(0.1)
        finally:
            self._lib.stopScan(self._handle)

        return devices

    def connect(self, device_name: str, scan_timeout: float = 10.0) -> None:
        """Connect to a specific device.

        Args:
            device_name: Name of the device to connect to.
            scan_timeout: Timeout for scanning in seconds (default: 10.0).

        Raises:
            SensorConnectionError: If connection fails or device not found.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise SensorConnectionError(msg)

        if self._lib.startScan(self._handle) != 0:
            msg = "Failed to start device scan"
            raise SensorConnectionError(msg)

        target = None
        t0 = time.time()

        try:
            while time.time() - t0 < scan_timeout:
                n = self._lib.getScannedNum(self._handle)
                for _ in range(n):
                    info = DeviceInfo()
                    if (
                        self._lib.getScannedDevice(self._handle, ctypes.byref(info))
                        == 0
                    ):
                        name = (
                            bytes(info.devicename)
                            .split(b"\x00", 1)[0]
                            .decode(errors="ignore")
                        )
                        if name == device_name:
                            target = info
                            break
                if target:
                    break
                time.sleep(0.1)
        finally:
            self._lib.stopScan(self._handle)

        if not target:
            msg = f"Device '{device_name}' not found"
            raise SensorConnectionError(msg)

        if self._lib.connect_device(self._handle, ctypes.byref(target)) != 0:
            msg = f"Failed to connect to device '{device_name}'"
            raise SensorConnectionError(msg)

        self._connected_device = target

    def start_measurement(self, enabled_channels: list[int] | None = None) -> int:
        """Start measurement.

        Args:
            enabled_channels: List of channel indices to enable (0-7).
                            If None, all channels are enabled.

        Returns:
            Device time in milliseconds since epoch.

        Raises:
            MeasurementError: If starting measurement fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        if self._connected_device is None:
            msg = "No device connected"
            raise MeasurementError(msg)

        sp = SensorParam()
        if enabled_channels is None:
            # Enable all channels
            for i in range(8):
                sp.usech[i] = 1
        else:
            for i in range(8):
                sp.usech[i] = 1 if i in enabled_channels else 0

        dummy_double = ctypes.c_double(0.0)
        devicetime_ll = ctypes.c_longlong(0)

        rc = self._lib.startMeasure(
            self._handle,
            ctypes.byref(sp),
            ctypes.byref(dummy_double),
            ctypes.byref(devicetime_ll),
        )

        if rc != 0:
            msg = f"startMeasure failed with error code: {rc}"
            raise MeasurementError(msg)

        self._measuring = True
        return int(devicetime_ll.value)

    def receive_data(self) -> Generator[ReceiveData2, None, None]:
        """Receive data from the sensor.

        Yields:
            ReceiveData2: Received data structure.

        Raises:
            MeasurementError: If measurement is not started.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        if not self._measuring:
            msg = "Measurement not started"
            raise MeasurementError(msg)

        recv = ReceiveData2()
        while self._measuring:
            num = self._lib.getReceiveNum(self._handle)
            if num <= 0:
                continue

            for _ in range(num):
                got = self._lib.getReceiveData2(self._handle, ctypes.byref(recv))
                if got >= 0:
                    yield recv

    def stop_measurement(self) -> None:
        """Stop measurement."""
        if self._handle is not None and self._measuring:
            self._lib.stopMeasure(self._handle)
            self._measuring = False

    def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._handle is not None and self._connected_device is not None:
            self.stop_measurement()
            self._lib.disconnect_device(self._handle)
            self._connected_device = None

    def close(self) -> None:
        """Close the sensor interface and release resources."""
        self.disconnect()
        if self._handle is not None:
            self._lib.Term(self._handle)
            self._handle = None

    @property
    def is_connected(self) -> bool:
        """Check if a device is connected."""
        return self._connected_device is not None

    @property
    def is_measuring(self) -> bool:
        """Check if measurement is active."""
        return self._measuring
