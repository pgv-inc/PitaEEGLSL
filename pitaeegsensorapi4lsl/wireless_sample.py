#!/usr/bin/env python3
"""Sample script for wireless EEG sensor data acquisition."""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import ClassVar

MAX_CH = 8
HARU2_CH_NUM = 3
MAX_DEVICENAME_LEN = 24
MAX_DEVICEADDR_LEN = 8


# ==== ctypes structs ====
class TIMESET_PARAM(ctypes.Structure):  # noqa: N801
    """Timeout parameters for communication and scanning."""

    _fields_: ClassVar = [("com_timeout", ctypes.c_int), ("scan_timeout", ctypes.c_int)]


class DEVICE_INFO(ctypes.Structure):  # noqa: N801
    """Device information structure."""

    _fields_: ClassVar = [
        ("deviceid", ctypes.c_ubyte * MAX_DEVICEADDR_LEN),
        ("devicename", ctypes.c_char * MAX_DEVICENAME_LEN),
    ]


class RECEIVE_DATA2(ctypes.Structure):  # noqa: N801
    """Received data structure for HARU2 sensor."""

    _fields_: ClassVar = [
        ("data", ctypes.c_double * HARU2_CH_NUM),
        ("batlevel", ctypes.c_double),
        ("isRepair", ctypes.c_ubyte),
    ]


class SENSOR_PARAM(ctypes.Structure):  # noqa: N801
    """Sensor parameter structure."""

    _fields_: ClassVar = [
        ("usech", ctypes.c_ubyte * MAX_CH),
        ("reserve", ctypes.c_ubyte * 32),
    ]


def _is_win() -> bool:
    return sys.platform.startswith("win")


def _is_mac() -> bool:
    return sys.platform.startswith("darwin")


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


BASE = "pitaeegsensor"


def load_library(explicit_path: str | None) -> ctypes.CDLL:
    """Load the native library from the specified path or default locations.

    Args:
        explicit_path: Path to the library file or directory containing it.

    Returns:
        ctypes.CDLL: Loaded library handle.

    Raises:
        OSError: If the library could not be found or loaded.

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
        for n in names:
            cand.extend([here / n, Path(n)])
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
    raise OSError(msg)


def bind_api(lib: ctypes.CDLL) -> ctypes.CDLL:
    """Bind API function signatures to the loaded library.

    Args:
        lib: ctypes.CDLL library handle.

    Returns:
        ctypes.CDLL: The library with bound function signatures.

    """
    lib.Init.argtypes = [ctypes.c_char_p, ctypes.POINTER(TIMESET_PARAM)]
    lib.Init.restype = ctypes.c_int

    lib.Term.argtypes = [ctypes.c_int]
    lib.Term.restype = ctypes.c_int

    lib.startScan.argtypes = [ctypes.c_int]
    lib.startScan.restype = ctypes.c_int

    lib.stopScan.argtypes = [ctypes.c_int]
    lib.stopScan.restype = ctypes.c_int

    lib.getScannedNum.argtypes = [ctypes.c_int]
    lib.getScannedNum.restype = ctypes.c_int

    lib.getScannedDevice.argtypes = [ctypes.c_int, ctypes.POINTER(DEVICE_INFO)]
    lib.getScannedDevice.restype = ctypes.c_int

    lib.connect_device.argtypes = [ctypes.c_int, ctypes.POINTER(DEVICE_INFO)]
    lib.connect_device.restype = ctypes.c_int

    lib.disconnect_device.argtypes = [ctypes.c_int]
    lib.disconnect_device.restype = ctypes.c_int

    # Wait for and get received data count
    lib.waitReceivedData.argtypes = [ctypes.c_int]
    lib.waitReceivedData.restype = ctypes.c_int

    lib.getReceiveNum.argtypes = [ctypes.c_int]
    lib.getReceiveNum.restype = ctypes.c_int

    lib.getReceiveData2.argtypes = [ctypes.c_int, ctypes.POINTER(RECEIVE_DATA2)]
    lib.getReceiveData2.restype = ctypes.c_int

    # startMeasure: SENSOR_PARAM*, double*, long long*
    lib.startMeasure.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(SENSOR_PARAM),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_longlong),
    ]
    lib.startMeasure.restype = ctypes.c_int

    lib.stopMeasure.argtypes = [ctypes.c_int]
    lib.stopMeasure.restype = ctypes.c_int
    return lib


def key_pressed_e() -> bool:
    """Check if the 'e' key has been pressed.

    Returns:
        bool: True if 'e' was pressed, False otherwise.

    """
    if _is_win():
        import msvcrt  # noqa: PLC0415

        return msvcrt.kbhit() and msvcrt.getwch().lower() == "e"  # type: ignore[attr-defined, no-any-return]
    import select  # noqa: PLC0415
    import termios  # noqa: PLC0415
    import tty  # noqa: PLC0415

    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch.lower() == "e"
    return False


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    """Acquire EEG sensor data and save to CSV file."""
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("sensor")
    ap.add_argument("--dll", help="DLL path or directory")
    ap.add_argument(
        "--out",
        default=None,
        help="Output file name (defaults to devicetime.csv if not specified)",
    )
    ap.add_argument("--scan-timeout", type=int, default=10)
    args = ap.parse_args()

    lib = bind_api(load_library(args.dll))
    print("[DBG] loaded:", getattr(lib, "_name", None))  # noqa: T201

    timeout = TIMESET_PARAM(com_timeout=2000, scan_timeout=5000)
    handle = lib.Init(args.port.encode("ascii"), ctypes.byref(timeout))
    if handle < 0:
        print(f"[ERROR] Init failed ({handle})")  # noqa: T201
        sys.exit(1)
    print("[OK] Init")  # noqa: T201

    # Scan for devices
    if lib.startScan(handle) != 0:
        print("[ERROR] startScan failed")  # noqa: T201
        lib.Term(handle)
        sys.exit(1)
    print(f"[OK] startScan. waiting {args.scan_timeout}s …")  # noqa: T201

    target = None
    t0 = time.time()
    while time.time() - t0 < args.scan_timeout:
        n = lib.getScannedNum(handle)
        for _ in range(n):
            info = DEVICE_INFO()
            if lib.getScannedDevice(handle, ctypes.byref(info)) == 0:
                name = (
                    bytes(info.devicename).split(b"\x00", 1)[0].decode(errors="ignore")
                )
                if name == args.sensor:
                    target = info
                    break
        if target:
            break
        time.sleep(0.1)
    lib.stopScan(handle)

    if not target:
        print(f"[ERROR] Sensor '{args.sensor}' not found")  # noqa: T201
        lib.Term(handle)
        sys.exit(1)

    if lib.connect_device(handle, ctypes.byref(target)) != 0:
        print("[ERROR] connect_device failed")  # noqa: T201
        lib.Term(handle)
        sys.exit(1)
    print("[OK] Connected")  # noqa: T201

    # ---- Start measurement: receive SENSOR_PARAM and devicetime ----
    sp = SENSOR_PARAM()
    for i in range(MAX_CH):
        sp.usech[i] = 1  # Enable all channels (HARU2 only has 3 channels with data)
    dummy_double = ctypes.c_double(0.0)  # Required by API spec: double*
    devicetime_ll = ctypes.c_longlong(0)

    rc = lib.startMeasure(
        handle,
        ctypes.byref(sp),
        ctypes.byref(dummy_double),
        ctypes.byref(devicetime_ll),
    )
    if rc != 0:
        print(f"[ERROR] startMeasure failed ({rc})")  # noqa: T201
        lib.disconnect_device(handle)
        lib.Term(handle)
        sys.exit(1)
    print("[OK] startMeasure")  # noqa: T201

    # --- After successful startMeasure (devicetime_ll contains device time in ms epoch) ---
    devicetime_ms = int(devicetime_ll.value)
    jst = timezone(timedelta(hours=9))
    t_base = datetime.fromtimestamp(devicetime_ms / 1000.0, tz=jst)

    # File name: YYYYMMDDhhmmss.csv (e.g., 20251008154425.csv)
    fn_stem = t_base.strftime("%Y%m%d%H%M%S")
    out_name = args.out or f"{fn_stem}.csv"
    out_path = Path(out_name).resolve()
    print(f"[INFO] writing to: {out_path}")  # noqa: T201

    # Create output directory if needed
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Header
    # Timestamp progression from here on
    next_ts_ms = devicetime_ms

    recv = RECEIVE_DATA2()
    with out_path.open("w", encoding="utf-8", newline="") as f:
        f.write("datetime,ChZ,ChR,ChL,bat,isRepair\n")

        try:
            print("[INFO] Receiving... press 'e' to stop.")  # noqa: T201
            while True:
                num = lib.getReceiveNum(handle)
                if num <= 0:
                    if key_pressed_e():
                        break
                    continue

                for _ in range(num):
                    got = lib.getReceiveData2(handle, ctypes.byref(recv))
                    if got < 0:
                        continue

                    # 3 channels
                    ch_z, ch_r, ch_l = (
                        float(recv.data[0]),
                        float(recv.data[1]),
                        float(recv.data[2]),
                    )
                    bat = float(recv.batlevel)
                    is_repair = int(recv.isRepair)

                    # Time in ISO format (e.g., 2024-09-19T10:04:14.643+09:00)
                    ts = datetime.fromtimestamp(next_ts_ms / 1000.0, tz=jst)
                    iso = ts.isoformat(timespec="milliseconds")
                    f.write(
                        f"{iso},{ch_z:.6f},{ch_r:.6f},{ch_l:.6f},{bat:.3f},{is_repair}\n",
                    )

                    # Next is +4ms
                    next_ts_ms += 4

                if key_pressed_e():
                    break

                time.sleep(0.001)

        finally:
            lib.stopMeasure(handle)
            lib.disconnect_device(handle)
            lib.Term(handle)
            print("[DONE] stopped and terminated")  # noqa: T201


if __name__ == "__main__":
    main()
