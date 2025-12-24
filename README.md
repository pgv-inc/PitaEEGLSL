---

## Non-medical Disclaimer (Important)

This software and the associated PitaEEG sensors are **not medical devices**.

- This package is **not intended for diagnosis, treatment, prevention, or mitigation of any disease or medical condition**.
- Results obtained using this software **must not be used for clinical decision-making**.
- Use in clinical workflows, patient diagnosis, or regulated medical contexts is **explicitly discouraged**.
- This software is intended solely for **research, evaluation, education, and prototyping purposes**.

Users are responsible for ensuring that their use of this software complies with applicable laws, regulations, and institutional review requirements.

---

## System Architecture

![System Architecture](pitaeeg.png)

**Data flow:**

```
PitaEEG Sensor
   ↓
PitaEEG Native API (C/C++)
   ↓
Python wrapper (pitaeeg)
   ↓
LabStreamingLayer (LSL)
   ↓
Downstream tools (LabRecorder, MNE, custom pipelines)
```

---

## Requirements

- Python > 3.11, < 4.0
- make >= 4.3
- Poetry >= 2.1 (for development)

---

## Installation

### From PyPI (Recommended)

```bash
pip install pitaeeg
```

### From GitHub

#### Poetry

```toml
pitaeeg = { git = "https://github.com/pgv-inc/PitaEEGLSL.git", rev = "0.12.0" }
```

```bash
poetry install
```

#### pip

```bash
pip install git+https://github.com/pgv-inc/PitaEEGLSL.git@0.12.0
```

---

## Native Library Setup

> **Important**: The native API library is proprietary and requires a license.

Once you have obtained the native library, place it under the `libs/` directory:

```text
libs/
├── linux/
│   └── libpitaeeg.so
├── macos/
│   ├── arm64/
│   │   └── libpitaeeg.dylib
│   └── x86_64/
│       └── libpitaeeg.dylib
└── windows/
    └── pitaeeg.dll
```

The library is automatically loaded based on the detected platform.

---

## Quick Start

```python
from pitaeeg import Sensor

with Sensor(port="COM3") as sensor:
    sensor.connect("HARU2-001", scan_timeout=10.0)
    sensor.start_measurement()

    for data in sensor.receive_data():
        print(data.data)
        break
```

---

## Usage Examples

### Scan for Available Devices

```python
from pitaeeg import Sensor

with Sensor(port="COM3") as sensor:
    devices = sensor.scan_devices(timeout=10.0)
    for device in devices:
        print(f"{device['name']} ({device['id']})")
```

### Save Data to CSV

```bash
python examples/wireless_acquisition.py COM3 HARU2-001 --out output.csv
```

---

## API Overview

### Sensor

**Constructor**

```python
Sensor(
    port: str,
    library_path: str | None = None,
    com_timeout: int = 2000,
    scan_timeout: int = 5000,
)
```

**Core Methods**

- `scan_devices(timeout=10.0)`
- `connect(device_name, scan_timeout=10.0)`
- `start_measurement(enabled_channels=None)`
- `receive_data()`
- `stop_measurement()`
- `disconnect()`
- `close()`

**Properties**

- `is_connected`
- `is_measuring`

---

## Error Handling

All exceptions inherit from `PitaEEGSensorError`:

- `LibraryNotFoundError`
- `InitializationError`
- `ScanError`
- `SensorConnectionError`
- `MeasurementError`

---

## Development

This project follows modern Python OSS best practices:

- Static typing (`mypy`)
- Automated linting and formatting (`ruff`)
- CI with GitHub Actions
- Coverage tracking

### Setup

```bash
make precommit-install
```

### Run checks

```bash
make check
```

### Run tests

```bash
make pytest
```

---

## Contributing

Contributions are welcome.  
Please read [CONTRIBUTING.md](.github/CONTRIBUTING.md) before submitting a pull request.

---

## License

MIT License  
See [LICENSE](LICENSE) for details.

---

## Security

For security-related issues, see [SECURITY.md](SECURITY.md).

---

## Design Philosophy: Why LabStreamingLayer (LSL)?

PitaEEGLSL is intentionally designed around **LabStreamingLayer (LSL)** rather than providing a bespoke streaming or file-based interface.

The rationale is as follows:

### Why LSL?

LSL has become a **de facto standard** in neuroscience and psychophysiology research for real-time data synchronization.  
By adopting LSL, PitaEEGLSL enables:

- **Time-synchronized multimodal experiments**  
  EEG data can be aligned with behavioral tasks, eye tracking, motion capture, or physiological signals.
- **Interoperability with existing tools**  
  Compatible with LabRecorder, MNE, EEGLAB, BCILAB, and custom LSL-based pipelines.
- **Reproducible research workflows**  
  Separation of acquisition, recording, and analysis improves experimental transparency.
- **Low-latency, real-time streaming**  
  Suitable for neurofeedback, online analysis, and closed-loop experiments.

### Design Principles

- **Thin Python wrapper**  
  The Python layer intentionally avoids duplicating logic already handled by the native API or LSL.
- **Explicit lifecycle management**  
  Context managers ensure deterministic resource cleanup.
- **Research-first ergonomics**  
  APIs favor clarity and robustness over convenience shortcuts.

This design allows PitaEEGLSL to integrate naturally into existing LSL-based research ecosystems rather than creating a parallel, incompatible workflow.

---

## Academic Use & Citation

If you use **PitaEEGLSL** or **PitaEEG sensors** in academic research, please cite the software and hardware appropriately.

### Software Citation

```bibtex
@software{pitaeeglsl,
  title        = {PitaEEGLSL: Python interface for PitaEEG and LabStreamingLayer},
  author       = {{PGV Inc.}},
  year         = {2025},
  url          = {https://github.com/pgv-inc/PitaEEGLSL}
}
```

### Hardware Reference

Please refer to PitaEEG hardware documentation provided by PGV Inc. when describing experimental apparatus.

If you publish work using this software, we welcome links to your publications via GitHub Discussions.

---

## FAQ (Frequently Asked Questions)

### Q1. Can I use this package without PitaEEG hardware?

No.  
This package requires **both** the PitaEEG sensor hardware and a licensed native API library.

---

### Q2. Can I use this without LabStreamingLayer (LSL)?

LSL is a core design assumption of this package.  
While the Python API exposes raw data objects, the intended use is **LSL-based streaming**.

---

### Q3. Is this package suitable for clinical or diagnostic use?

No.  
This software is intended for **research and development purposes only** and is **not certified as a medical device or SaMD**.

---

### Q4. Does this package support offline data analysis?

Data recording is typically handled via **LabRecorder** or other LSL-compatible tools.  
Offline analysis should be performed on recorded data using external toolchains (e.g., MNE, EEGLAB).

---

### Q5. Where should I report bugs or ask questions?

- Bug reports: GitHub Issues  
- Usage questions: GitHub Discussions  

Please include your OS, Python version, and hardware model when reporting issues.

---

## README（日本語概要）

### 本ライブラリについて

**PitaEEGLSL** は、PitaEEG 脳波センサーから取得したデータを  
**LabStreamingLayer（LSL）** を用いてリアルタイム配信するための Python ライブラリです。

研究用途・開発用途において、以下を目的としています。

- 脳波データのリアルタイム取得
- LSL を用いた他モダリティとの時間同期
- 既存の神経科学ツールチェーンとの統合

### 利用対象者

- LSL を用いた実験を行う研究者
- PitaEEG センサーを Python から制御したい開発者
- EEG を用いたリアルタイム解析・可視化・ML パイプライン構築者

### 重要な注意事項

本ライブラリは **Python ラッパー部分のみ** を提供します。  
以下は別途必要となります。

- PitaEEG センサーハードウェア
- PitaEEG ネイティブ API（ライセンス提供）

これらがない場合、本ライブラリは動作しません。

### 研究用途について

- 本ソフトウェアは **医療機器ではありません**
- 診断・治療目的での使用は想定していません
- 研究・評価・プロトタイピング用途に限定されます

---

## PyPI long_description Notes

This README is optimized to serve directly as the PyPI `long_description`:

- Clear audience definition at the top
- Early disclosure of proprietary dependencies
- Concise Quick Start
- Explicit research and non-clinical scope
- Citation and FAQ sections to reduce Issues

When publishing to PyPI, ensure:

- `long_description = file: README.md`
- `long_description_content_type = text/markdown`
