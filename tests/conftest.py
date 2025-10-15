# @see https://docs.pytest.org/en/latest/how-to/writing_hook_functions.html


import pytest
from dotenv import load_dotenv

load_dotenv()


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
    # --runslow オプションが無ければ無視します。
    if config.getoption("--runslow"):
        return

    if config.getoption("--deprecate"):
        return
    # 独自のスキップマーカー
    skip_runslow = pytest.mark.skip(reason="The option --runslow is required to run.")
    skip_deprecate = pytest.mark.skip(
        reason="The option --deprecate is required to run."
    )

    # 全テスト対象のメソッドを走査
    for item in items:
        # 'runslow'マーカーがあればスキップマーカーを付与
        if "runslow" in item.keywords:
            item.add_marker(skip_runslow)
        # 'runml'マーカーがあればスキップマーカーを付与
        elif "deprecate" in item.keywords:
            item.add_marker(skip_deprecate)
