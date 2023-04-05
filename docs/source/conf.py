# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'umodel_tools'
copyright = '2023, Skarn'  # pylint: disable=redefined-builtin
author = 'Skarn'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinx.ext.napoleon']

# autodoc configuration
autodoc_preserve_defaults = True

# general configuration
templates_path = ['_templates']
exclude_patterns = []

# output configuration
html_theme = "pydata_sphinx_theme"

html_static_path = ['_static']
