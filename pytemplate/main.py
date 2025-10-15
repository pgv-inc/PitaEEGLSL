"""Purpose: Main entry point for the pytemplate package."""

import logging

from pytemplate import __version__


def main() -> None:
    """Perform a specific task.

    Args:
    ----
        src (str): The source parameter.
        dst (str): The destination parameter.
        **kwargs (dict[str, Any]): Additional keyword arguments.

    Returns:
    -------
        None

    """
    logging.debug("version: %s", __version__)
