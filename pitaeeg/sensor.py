"""Core sensor API for PitaEEGSensor."""

from __future__ import annotations

import contextlib
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
from .types import (
    ContactResistance,
    DeviceInfo,
    ReceiveData2,
    SensorParam,
    TimesetParam,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType


def _is_win() -> bool:
    """Check if the current platform is Windows.

    Returns:
        bool: True if running on Windows, False otherwise.

    """
    return sys.platform.startswith("win")


def _is_mac() -> bool:
    """Check if the current platform is macOS.

    Returns:
        bool: True if running on macOS, False otherwise.

    """
    return sys.platform.startswith("darwin")


def _is_linux() -> bool:
    """Check if the current platform is Linux.

    Returns:
        bool: True if running on Linux, False otherwise.

    """
    return sys.platform.startswith("linux")


def _get_machine() -> str:
    """Get machine architecture string.

    Returns:
        str: Machine architecture in lowercase (e.g., 'arm64', 'x86_64').

    """
    return platform.machine().lower()


def _load_library(explicit_path: str | None = None) -> ctypes.CDLL:  # noqa: C901, PLR0912
    """Load the native library from the specified path or default locations.

    This function searches for the native library in the following order:
    1. If explicit_path is provided, searches in that location
    2. Platform-specific libs directory (e.g., libs/macos/arm64/)
    3. Package directory
    4. Current working directory

    On Windows, it uses os.add_dll_directory if available (Python 3.8+)
    to ensure proper DLL loading.

    Args:
        explicit_path: Optional path to the library file or directory containing it.
            If a directory is provided, standard library names are searched.
            If None, default search locations are used.

    Returns:
        ctypes.CDLL: Loaded library handle ready for use.

    Raises:
        LibraryNotFoundError: If the library could not be found or loaded
            in any of the search locations.

    """
    # If a directory is passed, search within it (try with 'd' suffix too)
    names = (
        ["pitaeeg.dll", "pitaeegd.dll"]
        if _is_win()
        else ["libpitaeeg.dylib", "libpitaeegd.dylib"]
        if _is_mac()
        else ["libpitaeeg.so", "libpitaeegd.so"]
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

    last: OSError | None = None

    for c in cand:
        if not c.exists():
            continue
        try:
            # 絶対パスにしてから使う
            c_abs = c.resolve()

            if _is_win():
                parent = c_abs.parent

                # os.add_dll_directory が存在する場合だけ使う(Python 3.8+)
                add_dll_directory = getattr(os, "add_dll_directory", None)
                if callable(add_dll_directory):
                    # AddDllDirectory には絶対パスを渡す
                    with add_dll_directory(str(parent)):
                        return ctypes.CDLL(str(c_abs))
                # 古い Python などで add_dll_directory が無い場合
                return ctypes.CDLL(str(c_abs))

            # Windows 以外
            return ctypes.CDLL(str(c_abs))
        except OSError as e:
            last = e

    msg = f"Native lib not found. Tried: {[str(x) for x in cand]}. Last: {last}"
    raise LibraryNotFoundError(msg)


def _bind_api(lib: ctypes.CDLL) -> ctypes.CDLL:
    """Bind API function signatures to the loaded library.

    This function configures the ctypes function signatures (argtypes and restype)
    for all native API functions in the library. This is required for proper
    type checking and parameter passing when calling native functions.

    Args:
        lib: Raw ctypes.CDLL library handle loaded from the native library file.

    Returns:
        ctypes.CDLL: The same library handle with all function signatures bound.
            This allows for type-safe calls to native API functions.

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

    # startMeasure2: long long*
    lib.startMeasure2.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_longlong),
    ]
    lib.startMeasure2.restype = ctypes.c_int

    lib.stopMeasure.argtypes = [ctypes.c_int]
    lib.stopMeasure.restype = ctypes.c_int

    # int getPgvSensorBatteryRemainingTime(int handle , double *battery);
    lib.getPgvSensorBatteryRemainingTime.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.getPgvSensorBatteryRemainingTime.restype = ctypes.c_int

    # int getPgvSensorVersion(int handle,double  *version);
    lib.getPgvSensorVersion.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.getPgvSensorVersion.restype = ctypes.c_int

    # int getSensorState(int handle, int *state, int *error);
    lib.getSensorState.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.getSensorState.restype = ctypes.c_int

    # int getContactResistance(int handle, CONTACT_RESISTANCE *resistance);
    lib.getContactResistance.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ContactResistance),
    ]
    lib.getContactResistance.restype = ctypes.c_int
    return lib


class Sensor:
    """PitaEEGSensor interface.

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
        com_timeout: int = 5000,
        scan_timeout: int = 5000,
    ) -> None:
        """Initialize the sensor interface.

        Args:
            port: Serial port name (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux).
            library_path: Optional path to the native library file or directory.
            com_timeout: Communication timeout in milliseconds (default: 5000).
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
        """Context manager exit.

        Ensures that resources are properly cleaned up when exiting a context.
        This method calls :meth:`close` to stop measurement, disconnect devices,
        and release all resources.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise.
            exc_val: Exception value if an exception occurred, None otherwise.
            exc_tb: Traceback if an exception occurred, None otherwise.

        """
        self.close()

    def scan_devices(self, timeout: float = 10.0) -> list[dict[str, str]]:
        """Scan for available devices.

        Initiates a device scan operation to discover PitaEEG sensors that are
        within communication range. The scan continues until devices are found
        or the timeout expires.

        Args:
            timeout: Maximum time to wait for devices in seconds (default: 10.0).
                The scan will stop early if devices are found before the timeout.

        Returns:
            list[dict[str, str]]: List of dictionaries containing device information.
                Each dictionary contains:
                - ``name`` (str): Device name (e.g., "HARU2-001")
                - ``id`` (str): Device ID as a hexadecimal string

        Raises:
            ScanError: If the sensor is not initialized or scanning fails.

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

        Scans for devices and connects to the device matching the specified name.
        This method must be called before starting measurements. Use
        :meth:`scan_devices` to discover available device names.

        Args:
            device_name: Name of the device to connect to (e.g., "HARU2-001").
                This should match one of the device names returned by
                :meth:`scan_devices`.
            scan_timeout: Maximum time to wait for the device to be found
                in seconds (default: 10.0).

        Raises:
            SensorConnectionError: If the sensor is not initialized, device
                scanning fails, the device is not found, or connection fails.

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

    def start_measurement(self) -> int:
        """Start EEG measurement.

        Starts measurement using all available channels. This method must be
        called after a device has been connected via :meth:`connect`.
        After starting measurement, data can be received using :meth:`receive_data`.

        The returned device time represents the timestamp from the sensor device
        when measurement began, allowing synchronization with the device clock.

        Returns:
            int: Device time in milliseconds since epoch (Unix timestamp * 1000).
                This timestamp represents when the sensor device started measurement.

        Raises:
            MeasurementError: If the sensor is not initialized, no device is
                connected, or starting measurement fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        if self._connected_device is None:
            msg = "No device connected"
            raise MeasurementError(msg)

        devicetime_ll = ctypes.c_longlong(0)

        rc = self._lib.startMeasure2(
            self._handle,
            ctypes.byref(devicetime_ll),
        )

        if rc != 0:
            msg = f"startMeasure failed with error code: {rc}"
            raise MeasurementError(msg)

        self._measuring = True
        return int(devicetime_ll.value)

    def receive_data(self) -> Generator[ReceiveData2, None, None]:
        """Receive data from the sensor.

        This method returns a generator that yields EEG data packets as they
        become available from the sensor. The generator will continue to yield
        data until measurement is stopped via :meth:`stop_measurement`.

        Each yielded :class:`ReceiveData2` object contains:
        - EEG channel data (3 channels for HARU2)
        - Battery level percentage
        - Data repair/correction flag

        Note:
            This method blocks until data is available. To stop receiving data,
            call :meth:`stop_measurement` from another thread or use a timeout
            mechanism.

        Yields:
            ReceiveData2: Received data structure containing EEG measurements
                and sensor status information.

        Raises:
            MeasurementError: If the sensor is not initialized or measurement
                is not started.

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
        """Stop ongoing EEG measurement.

        Stops measurement only if the device is initialized and currently
        measuring. If no measurement is active, this function does nothing.

        Raises:
            MeasurementError: Not raised directly here, but subsequent API
                calls depending on measurement state may fail if measurement
                was never started.

        """
        if self._handle is not None and self._measuring:
            self._lib.stopMeasure(self._handle)
            self._measuring = False

    def disconnect(self) -> None:
        """Disconnect from the EEG device.

        If a measurement is active, it will be stopped first. After
        disconnecting, the internal connection state is cleared.

        Raises:
            SensorConnectionError: If the sensor was never connected.
                (i.e., `_connected_device` is None)

        """
        if self._handle is not None and self._connected_device is not None:
            self.stop_measurement()
            self._lib.disconnect_device(self._handle)
            self._connected_device = None

    def close(self) -> None:
        """Close the sensor interface and release resources.

        This method attempts to safely stop measurement, disconnect the
        device, and terminate the sensor handle. All operations are
        best-effort and any internal errors are ignored. This function
        never raises exceptions.

        Notes:
            - If measurement is active, it will be stopped.
            - If a device is connected, it will be disconnected.
            - If a handle is present, it will be terminated.
            - If any step fails, the error is silently ignored.

        """
        with contextlib.suppress(Exception):
            self.disconnect()

        if self._handle is not None:
            with contextlib.suppress(Exception):
                self._lib.Term(self._handle)
            self._handle = None

    def get_battery_remaining_time(self) -> float:
        """Return remaining battery time.

        The returned value represents the estimated remaining battery time in minutes.

        Returns:
            float: Remaining battery time in minutes.

        Raises:
            MeasurementError: If the sensor is not initialized or if the operation
            fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        value = ctypes.c_double(0.0)
        rc = self._lib.getPgvSensorBatteryRemainingTime(
            self._handle,
            ctypes.byref(value),
        )
        if rc != 0:
            msg = f"getPgvSensorBatteryRemainingTime failed with error code: {rc}"
            raise MeasurementError(msg)

        return float(value.value)

    def get_version(self) -> float:
        """Return sensor firmware version.

        The version is returned as a floating-point number.

        Returns:
            float: Firmware version value from the device.

        Raises:
            MeasurementError: If the sensor is not initialized or the
                native API call fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        value = ctypes.c_double(0.0)
        rc = self._lib.getPgvSensorVersion(
            self._handle,
            ctypes.byref(value),
        )
        if rc != 0:
            msg = f"getPgvSensorVersion failed with error code: {rc}"
            raise MeasurementError(msg)

        return float(value.value)

    def get_state(self) -> tuple[int, int]:
        """Get the current sensor state and error code.

        Returns:
            tuple[int, int]: A tuple ``(state, error)`` where:

            **Sensor State (SENSOR_STATE)**
            Represents the operating status of the EEG device.

            - INITIAL (0): Initial state
            - WAIT_CONNECT (1): Waiting for device connection
            - IDLE (2): Waiting to start measurement
            - MEASURE (3): Measuring via wireless mode
            - STORE (4): Measuring in storage mode
            - ERR (0x80 / 128): Error state flag

            Multiple states may be combined using a logical OR.

            **Sensor Error (SENSOR_ERROR)**
            Represents abnormal conditions detected by the device.

            - ELECTRODE_NOT_CONNECTED (0x01): Electrode sheet not connected
            - AFE_COMM_ERROR (0x02): Hardware communication error ※
            - BLE_IC_COMM_ERROR_CMD (0x03): BLE IC command communication error ※
            - BLE_IC_COMM_ERROR_DATA (0x04): BLE IC data communication error ※
            - CHARGE_ERROR (0x05): Charging-related hardware error ※
            - BATTERY_REMAINING_ERROR (0x06): Battery remaining below 5%
            - STORAGE_ERROR (0x07): Failed to save data to storage
            - BLE_COMM_ERROR (0x08): BLE communication hardware error ※
            - USB_COMM_ERROR (0x09): USB communication hardware error ※
            - ERROR_END (0x0A): General hardware error flag ※

            ※ If this error occurs, please contact PGV support.

        Raises:
            MeasurementError: If the sensor is not initialized or the API call fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        state = ctypes.c_int(0)
        err = ctypes.c_int(0)
        rc = self._lib.getSensorState(
            self._handle,
            ctypes.byref(state),
            ctypes.byref(err),
        )
        if rc != 0:
            msg = f"getSensorState failed with error code: {rc}"
            raise MeasurementError(msg)

        return int(state.value), int(err.value)

    def get_contact_resistance(self) -> ContactResistance:
        """Retrieve electrode contact-resistance data.

        Returns:
            ContactResistance: Structure containing raw resistance values
                (e.g., ChZ, ChR, ChL). The value is expressed in ohms (Ω).

        Raises:
            MeasurementError: If the sensor is not initialized or the
                native API call fails.

        """
        if self._handle is None:
            msg = "Sensor not initialized"
            raise MeasurementError(msg)

        res = ContactResistance()
        rc = self._lib.getContactResistance(
            self._handle,
            ctypes.byref(res),
        )
        if rc != 0:
            msg = f"getContactResistance failed with error code: {rc}"
            raise MeasurementError(msg)

        return res

    @property
    def is_connected(self) -> bool:
        """Check if a device is currently connected.

        Returns:
            bool: True if a device is connected, False otherwise.

        """
        return self._connected_device is not None

    @property
    def is_measuring(self) -> bool:
        """Check if measurement is currently active.

        Returns:
            bool: True if measurement is active, False otherwise.

        """
        return self._measuring
