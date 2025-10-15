# pitaeegsensorapi4lsl

Python package template with poetry

[![Python check](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/pythonpackage.yml)

## Requirements

- make >=4.3
- Python >3.11, <4.0
- Poetry >=2.1

## Installation

- Poetry(pyproject.toml)

```toml
pitaeegsensorapi4lsl = {git = "https://github.com/kezure/pitaeegsensorapi4lsl.git", rev = "0.1.0"}
```

```bash
poetry install
```

- pip

```bash
pip install git+https://github.com/kezure/pitaeegsensorapi4lsl.git@0.1.0
```

### Native Library Setup

The native API library must be placed in the `libs/` directory according to your platform:

```
libs/
├── linux/
│   └── libpitaeegsensor.so (or libpitaeegsensor.so.x.x.x)
├── macos/
│   ├── arm64/
│   │   └── libpitaeegsensor.dylib (or libpitaeegsensor.x.x.x.dylib)
│   └── x86_64/
│       └── libpitaeegsensor.dylib (or libpitaeegsensor.x.x.x.dylib)
└── windows/
    └── pitaeegsensor.dll (or pitaeegsensord.dll)
```

The library will be automatically loaded from the appropriate platform directory.

## Usage

```python
import pitaeegsensorapi4lsl

pitaeegsensorapi4lsl.hello()
```

## Development

### Format&Lint(pre-commit)

```bash
make precommit-install
```

```bash
make check
```

### Test

```bash
make pytest
```

```bash
make pytest-dist
```

```bash
make coverage
```

```bash
make coverage-dist
```
