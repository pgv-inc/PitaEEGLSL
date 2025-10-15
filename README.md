# pitaeegsensorapi4lsl

Python package template with poetry

[![Python check](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/pythonpackage.yml)
[![Docker Build and Test](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/kezure/pitaeegsensorapi4lsl/actions/workflows/build_and_test.yml)

## Requirements

- make >=4.3
- Python >3.11, <4.0
- Poetry >=2.1
- Docker >=27

## Usage template

- Replace `pitaeegsensorapi4lsl` with your package name

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
