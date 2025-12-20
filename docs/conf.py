# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../lib/awdur"))

import awdur

project = "Awdur"
copyright = "2025, Alex Carney"
author = "Alex Carney"
release = awdur.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "awdur.sphinxext",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "furo"
html_title = "Awdur"
# html_logo = "../resources/io.github.swyddfa.Esbonio.svg"
# html_favicon = "favicon.svg"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/swyddfa/awdur/",
    "source_branch": "develop",
    "source_directory": "docs/",
}
