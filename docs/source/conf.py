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
# Handle authors (can be list or string)
authors_config = config.get("authors", [])
if isinstance(authors_config, list) and len(authors_config) > 0:
    if isinstance(authors_config[0], dict):
        author = authors_config[0].get("name", "Unknown")
    else:
        author = str(authors_config[0])
else:
    author = str(authors_config) if authors_config else "Unknown"
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

# Read the Docs settings
html_baseurl = "https://pitaeeg.readthedocs.io/"

# Additional HTML options
html_title = f"{project} {version} documentation"
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True
