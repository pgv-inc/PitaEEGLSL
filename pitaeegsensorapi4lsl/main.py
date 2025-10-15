"""Purpose: Main entry point for the pitaeegsensorapi4lsl package."""

import logging

from pitaeegsensorapi4lsl import __version__


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
