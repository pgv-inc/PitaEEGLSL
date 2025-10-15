# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

from sphinx_pyproject import SphinxConfig

sys.path.append(os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../../"))
config = SphinxConfig("../../pyproject.toml", globalns=globals())

project = config.name
version = config.version
description = config.description
author = config.author
copyright = config["copyright"]
project_copyright = config["copyright"]

# # -- General configuration ---------------------------------------------------
# # https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = config["extensions"]
templates_path = config["templates_path"]
exclude_patterns = config["exclude_patterns"]
language = config["language"]

# # -- Options for HTML output -------------------------------------------------
# # https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = config["html_theme"]
html_static_path = config["html_static_path"]
