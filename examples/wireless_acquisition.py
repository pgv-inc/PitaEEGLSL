#!/usr/bin/env python3
"""Example: Acquire EEG sensor data and save to CSV file."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pitaeeg import PitaEEGSensorError, Sensor


def key_pressed_e() -> bool:
    """Check if the 'e' key has been pressed.

    Returns:
        bool: True if 'e' was pressed, False otherwise.

    """
    if sys.platform.startswith("win"):
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


def main() -> None:  # noqa: PLR0915
    """Acquire EEG sensor data and save to CSV file."""
    ap = argparse.ArgumentParser(
        description="Acquire EEG sensor data from PitaEEGSensor",
    )
    ap.add_argument("port", help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    ap.add_argument("sensor", help="Sensor name to connect to (e.g., HARU2-001)")
    ap.add_argument("--dll", help="Path to native library file or directory",default=None)
    ap.add_argument(
        "--out",
        default=None,
        help="Output file name (defaults to YYYYMMDDhhmmss.csv if not specified)",
    )
    ap.add_argument(
        "--scan-timeout",
        type=int,
        default=10,
        help="Device scan timeout in seconds (default: 10)",
    )
    args = ap.parse_args()

    print(f"[INFO] Initializing sensor on port {args.port}...")  # noqa: T201

    # Initialize sensor
    try:
        with Sensor(port=args.port, library_path=args.dll) as sensor:
            print("[OK] Sensor initialized")  # noqa: T201

            # Connect to device
            print(  # noqa: T201
                f"[INFO] Scanning for device '{args.sensor}' (timeout: {args.scan_timeout}s)...",
            )
            sensor.connect(args.sensor, scan_timeout=args.scan_timeout)
            print(f"[OK] Connected to '{args.sensor}'")  # noqa: T201

            # Start measurement
            devicetime_ms = sensor.start_measurement()

            # Prepare output file
            jst = timezone(timedelta(hours=9))
            t_base = datetime.fromtimestamp(devicetime_ms / 1000.0, tz=jst)
            print(f"[OK] Measurement started (device time: {t_base})")  # noqa: T201

            # File name: YYYYMMDDhhmmss.csv (e.g., 20251008154425.csv)
            fn_stem = t_base.strftime("%Y%m%d%H%M%S")
            out_name = args.out or f"{fn_stem}.csv"
            out_path = Path(out_name).resolve()
            print(f"[INFO] Writing to: {out_path}")  # noqa: T201

            # Create output directory if needed
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Timestamp progression from here on
            next_ts_ms = devicetime_ms

            # Open file and write data
            with out_path.open("w", encoding="utf-8", newline="") as f:
                f.write("datetime,ChZ,ChR,ChL,bat,isRepair\n")

                print("[INFO] Receiving data... press 'e' to stop.")  # noqa: T201

                try:
                    for recv in sensor.receive_data():
                        # 3 channels
                        ch_z = float(recv.data[0])
                        ch_r = float(recv.data[1])
                        ch_l = float(recv.data[2])
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
                            print("\n[INFO] Stop requested by user")  # noqa: T201
                            break

                        time.sleep(0.001)

                except KeyboardInterrupt:
                    print("\n[INFO] Interrupted by user")  # noqa: T201

            print(f"[DONE] Data saved to {out_path}")  # noqa: T201

    except PitaEEGSensorError as e:
        print(f"[ERROR] {e}")  # noqa: T201
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")  # noqa: T201
        sys.exit(0)


if __name__ == "__main__":
    main()
