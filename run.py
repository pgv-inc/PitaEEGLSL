"""Purpose: Run the application."""

import argparse
import logging

from pytemplate import __version__


def main(src: str, dst: str) -> None:
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
    logging.debug("src: %s", src)
    logging.debug("dst: %s", dst)
    logging.debug("version: %s", __version__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=str, required=True)
    parser.add_argument("--dst", type=str, default="")
    args = parser.parse_args()
    logging.info("args: %s", args)

    main(**vars(args))
