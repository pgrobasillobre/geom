# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'geom'
copyright = '2025, Pablo Grobas Illobre'
author = 'Pablo Grobas Illobre'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'autoapi.extension',  # For AutoAPI
]

autoapi_type = 'python'
autoapi_dirs = ['../geom']


templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',  # Use your own custom styles
]

html_logo = "_static/geom-logo-autogen.png"


napoleon_google_docstring = True
napoleon_numpy_docstring = False

html_theme_options = {
    "logo_only": False,
}

