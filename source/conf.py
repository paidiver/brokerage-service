"""Sphinx configuration for the Paidiver Image Brokerage Service portal."""

from pygments.lexer import RegexLexer
from pygments.token import Text
from sphinx.highlighting import lexers

project = "Paidiver Image Brokerage Service"
copyright = "2026, National Oceanography Centre"
author = "Ocean Informatics, National Oceanography Centre"
release = "1.0"

extensions = ["myst_parser", "sphinx_copybutton"]
myst_enable_extensions = ["colon_fence", "deflist", "substitution", "tasklist"]
myst_heading_anchors = 3

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
templates_path = ["_templates"]
exclude_patterns = ["repos/**/.github/**"]
suppress_warnings = [
    "misc.highlighting_failure",
    "myst.header",
    "myst.xref_missing",
]

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_js_files = ["open_repos_sidebar.js"]
html_logo = "_static/NOC-logo.svg"
html_title = "Paidiver Image Brokerage Service"
html_theme_options = {
    "home_page_in_toc": True,
    "repository_url": "https://github.com/paidiver/brokerage-service",
    "repository_branch": "main",
    "path_to_docs": "source",
    "use_repository_button": True,
    "use_issues_button": True,
}


class EnvLexer(RegexLexer):
    """Minimal lexer for dotenv examples."""

    name = "env"
    tokens = {"root": [(r".+", Text)]}


lexers["env"] = EnvLexer()
