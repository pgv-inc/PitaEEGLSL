#!/usr/bin/env python3
"""Example: Acquire EEG sensor data, save to CSV, and show filtered waveform & spectrogram."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import deque

import numpy as np
import matplotlib.pyplot as plt

from pitaeeg import PitaEEGSensorError, Sensor


def _design_fir_lowpass(fc: float, fs: float, num_taps: int) -> np.ndarray:
    """Windowed-sinc low-pass FIR."""
    fc_norm = fc / fs  # (cycles/sample)
    M = num_taps - 1
    n = np.arange(num_taps, dtype=float)
    h = 2 * fc_norm * np.sinc(2 * fc_norm * (n - M / 2))
    w = 0.54 - 0.46 * np.cos(2 * np.pi * n / M)  # Hamming
    h *= w
    h /= np.sum(h)  # DC ゲインを 1 に正規化
    return h


def _design_fir_highpass(fc: float, fs: float, num_taps: int) -> np.ndarray:
    """High-pass FIR via spectral inversion of low-pass."""
    h_lp = _design_fir_lowpass(fc, fs, num_taps)
    h_hp = -h_lp
    mid = num_taps // 2
    h_hp[mid] += 1.0
    return h_hp


def main() -> None:  # noqa: PLR0915
    """Acquire EEG sensor data and save to CSV file."""
    ap = argparse.ArgumentParser(
        description="Acquire EEG sensor data from PitaEEGSensor",
    )
    ap.add_argument("port", help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    ap.add_argument("sensor", help="Sensor name to connect to (e.g., HARU2-001)")
    ap.add_argument(
        "--dll",
        help="Path to native library file or directory",
        default=None,
    )
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
    ap.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Measurement duration in seconds (default: 30)",
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

            remaining_time = sensor.get_battery_remaining_time()
            print(f"[INFO] Battery remaining time: {remaining_time:.1f} [min]")  # noqa: T201

            # 2) センサーバージョン
            version = sensor.get_version()
            print(f"[INFO] Sensor version: {version:.3f}")  # noqa: T201

            # 3) センサー状態
            #    戻り値が (state, error) のタプルを想定
            state, error = sensor.get_state()
            print(f"[INFO] Sensor state: {state}, error: {error}")  # noqa: T201

            # 4) 接触抵抗
            #    ContactResistance 型（例: res.ch_z, res.ch_r, res.ch_l）を想定
            res = sensor.get_contact_resistance()
            # 型によって名前は合わせてください（ch_z / ChZ など）
            ch_z = getattr(res, "ch_z", getattr(res, "ChZ", None))
            ch_r = getattr(res, "ch_r", getattr(res, "ChR", None))
            ch_l = getattr(res, "ch_l", getattr(res, "ChL", None))

            print(
                "[INFO] Contact resistance:"
                f" ChZ={ch_z:.2f}, ChR={ch_r:.2f}, ChL={ch_l:.2f}"  # noqa: T201
            )

            # Start measurement
            devicetime_ms = sensor.start_measurement()

            # Prepare output file
            jst = timezone(timedelta(hours=9))
            t_base = datetime.fromtimestamp(devicetime_ms / 1000.0, tz=jst)
            print(f"[OK] Measurement started (device time: {t_base}ms)")  # noqa: T201

            # File name: YYYYMMDDhhmmss.csv (e.g., 20251008154425.csv)
            fn_stem = t_base.strftime("%Y%m%d%H%M%S")
            out_name = args.out or f"{fn_stem}.csv"
            out_path = Path(out_name).resolve()
            print(f"[INFO] Writing to: {out_path}")  # noqa: T201

            # Create output directory if needed
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Timestamp progression from here on (device time base)
            next_ts_ms = devicetime_ms

            # オフライン処理用に全サンプルをメモリに貯める
            times_ms: list[float] = []
            chz_list: list[float] = []
            chr_list: list[float] = []
            chl_list: list[float] = []
            bat_list: list[float] = []
            repair_list: list[int] = []

            fs = 250.0  # 4 ms per sample 前提

            # CSV 書き出し＋バッファリング
            with out_path.open("w", encoding="utf-8", newline="") as f:
                f.write("datetime,ChZ,ChR,ChL,bat,isRepair\n")

                print(
                    f"[INFO] Receiving data for {args.duration} sec ...",  # noqa: T201
                )

                start_wall = time.time()

                try:
                    for recv in sensor.receive_data():
                        now_wall = time.time()
                        if now_wall - start_wall >= args.duration:
                            print("\n[INFO] Measurement duration reached")  # noqa: T201
                            break

                        # 3 channels (raw)
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

                        # メモリにも保存（後で FIR & FFT 用）
                        times_ms.append(next_ts_ms)
                        chz_list.append(ch_z)
                        chr_list.append(ch_r)
                        chl_list.append(ch_l)
                        bat_list.append(bat)
                        repair_list.append(is_repair)

                        # Next is +4ms
                        next_ts_ms += 4

                        # ここでは 0.001 秒スリープをそのまま維持
                        time.sleep(0.001)

                except KeyboardInterrupt:
                    print("\n[INFO] Interrupted by user")  # noqa: T201

            print(f"[DONE] Data saved to {out_path}")  # noqa: T201

            # ---- 測定データが溜まったので FIR & FFT を実行 ----
            if not chz_list:
                print("[WARN] No data collected; nothing to plot.")  # noqa: T201
                return

            # numpy 配列化（3chまとめて扱う）
            chz = np.asarray(chz_list, dtype=float)
            chr_ = np.asarray(chr_list, dtype=float)
            chl = np.asarray(chl_list, dtype=float)

            data = np.vstack([chz, chr_, chl])  # shape: (3, N)
            labels = ["ChZ", "ChR", "ChL"]

            n_samples = data.shape[1]
            t = np.arange(n_samples) / fs  # 秒

            # FIR (HPF 0.5 Hz + LPF 40 Hz)
            hpf_cut = 0.5
            lpf_cut = 40.0

            NTAPS_HP = 251
            NTAPS_LP = 127

            h_hp = _design_fir_highpass(hpf_cut, fs, NTAPS_HP)
            h_lp = _design_fir_lowpass(lpf_cut, fs, NTAPS_LP)

            # 3ch 分バンドパス（0.5–40Hz）を適用
            filtered = np.zeros_like(data)
            for ch in range(3):
                hp = np.convolve(data[ch], h_hp, mode="same")
                bp = np.convolve(hp, h_lp, mode="same")
                filtered[ch] = bp

            # ---- プロット：フィルタ波形 (3ch) ----
            fig1, axes1 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
            fig1.suptitle("Filtered EEG (0.5–40 Hz)", fontsize=16)

            for ch in range(3):
                ax = axes1[ch]
                ax.plot(t, filtered[ch])
                ax.set_ylabel(labels[ch])
                ax.set_ylim(-500, 500)
                ax.invert_yaxis()

                if ch == 2:
                    ax.set_xlabel("Time [s]")

            fig1.tight_layout(rect=[0, 0.03, 1, 0.95])


            # ---- プロット：スペクトログラム (3ch) ----
            fig2, axes2 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
            fig2.suptitle("Spectrogram (0.5–40 Hz filtered)", fontsize=16)

            for ch in range(3):
                ax = axes2[ch]
                Pxx, freqs, bins, im = ax.specgram(
                    filtered[ch],
                    NFFT=256,
                    Fs=fs,
                    noverlap=128,
                    cmap="jet",
                    vmin=0, 
                    vmax=35
                )
                ax.set_ylim(0, 60)
                ax.set_ylabel(f"{labels[ch]}\nFreq [Hz]")
                if ch == 2:
                    ax.set_xlabel("Time [s]")

            fig2.tight_layout(rect=[0, 0.03, 1, 0.95])

            plt.show()

    except PitaEEGSensorError as e:
        print(f"[ERROR] {e}")  # noqa: T201
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")  # noqa: T201
        sys.exit(0)


if __name__ == "__main__":
    main()
