"""Documentation configuration script
"""

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'umodel_tools'
copyright = '2023, Skarn'  # pylint: disable=redefined-builtin
author = 'Skarn'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinx.ext.napoleon',
              'sphinx.ext.intersphinx']

intersphinx_mapping = {'python': ('https://docs.python.org/3', None),
                       'bpy': ('https://docs.blender.org/api/current/', None),
                       'lark': ('https://lark-parser.readthedocs.io/en/latest/', None)}

# autodoc configuration
autodoc_preserve_defaults = True
autodoc_typehints_format = 'fully-qualified'

# general configuration
templates_path = ['_templates']
exclude_patterns = []

# output configuration
html_theme = "pydata_sphinx_theme"
html_title = "UModel Tools"

html_theme_options = {
    'github_url': "https://github.com/skarndev/umodel_tools",
    'navigation_depth': 2
}

html_sidebars = {
    "**": ["sidebar-nav-bs", "sidebar-ethical-ads"],
    "index": [],
    "auto_examples/index": [],
}

html_static_path = ['_static']
