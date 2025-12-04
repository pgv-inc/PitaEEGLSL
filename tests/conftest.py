# @see https://docs.pytest.org/en/latest/how-to/writing_hook_functions.html

from __future__ import annotations

import contextlib
import sys
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

from pitaeeg import sensor  # sensor.py 内の os / ctypes などをパッチするため

# .env を読み込む（テスト全体で共通）
load_dotenv()

@pytest.fixture
def mock_lib() -> MagicMock:
    """Create a mock library for sensor tests.

    Returns:
        MagicMock: Mock library with default return values.
    """
    lib = MagicMock()
    lib.Init.return_value = 1  # Valid handle
    lib.Term.return_value = 0
    lib.startScan.return_value = 0
    lib.stopScan.return_value = 0
    lib.getScannedNum.return_value = 0
    lib.getScannedDevice.return_value = 0
    lib.connect_device.return_value = 0
    lib.disconnect_device.return_value = 0
    lib.startMeasure.return_value = 0
    lib.stopMeasure.return_value = 0
    lib.getReceiveNum.return_value = 0
    lib.getReceiveData2.return_value = 0
    lib.waitReceivedData.return_value = 0
    lib.startMeasure2.return_value = 0

    return lib


@contextlib.contextmanager
def _dummy_add_dll_directory(path: str):
    """Windows 用のダミー add_dll_directory（テスト時だけ使用）。

    本番では os.add_dll_directory を使うが、テスト中はモックされた Path
    などが渡されて WinError 87 が出るのを避けるため、何もしない CM に差し替える。
    """
    yield


@pytest.fixture(autouse=True)
def _patch_platform_specific(monkeypatch):
    """プラットフォーム依存部分をテストフレンドリーにする共通パッチ。

    - Windows: sensor.os.add_dll_directory を no-op に差し替える

    macOS / Linux では何もしない。
    """
    if sys.platform.startswith("win"):
        # sensor.os は pitaeeg.sensor 内で import された os モジュール
        if hasattr(sensor.os, "add_dll_directory"):
            monkeypatch.setattr(
                sensor.os,
                "add_dll_directory",
                _dummy_add_dll_directory,
            )


def pytest_addoption(parser):
    """Parse command line options
        True if --runslow,
        False otherwise
        Hold as a variable
    Args:
        parser (): args

    Returns
    -------
    """
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Run a test that takes a long time to run",
    )
    parser.addoption(
        "--deprecate",
        action="store_true",
        default=False,
        help="Deprecated class and method.",
    )


def pytest_configure(config):
    """$ pytest --markers
    Add a description of the markers that can be referenced with the above command.

    Args:
    ----
        config ():

    Returns:
    -------

    """    
    config.addinivalue_line(
        "markers", "runslow: Mark of a test that takes a long time to run"
    )
    config.addinivalue_line(
        "markers", "deprecate: Mark of a test that requires a machine learning model"
    )


def pytest_collection_modifyitems(session, config, items):
    """Apply automatic skipping based on command-line options.

    - --runslow  が無いとき: 'runslow' マーク付きテストを skip
    - --deprecate が無いとき: 'deprecate' マーク付きテストを skip
    """
    # --runslow / --deprecate が指定されていれば何もしない
    if config.getoption("--runslow") or config.getoption("--deprecate"):
        return

    skip_runslow = pytest.mark.skip(reason="The option --runslow is required to run.")
    skip_deprecate = pytest.mark.skip(
        reason="The option --deprecate is required to run."
    )

    for item in items:
        if "runslow" in item.keywords:
            item.add_marker(skip_runslow)
        elif "deprecate" in item.keywords:
            item.add_marker(skip_deprecate)
