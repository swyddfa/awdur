from __future__ import annotations

import logging
import pathlib
import tempfile
import typing

from jinja2 import Template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

from .directory import DirectoryExporter

if typing.TYPE_CHECKING:
    from . import Project
    from . import ProjectFile


HTML_TEMPLATE = """\
{%- macro render_dir(root) %}
  {%- for item in iter_dir(root) %}
    {%- if item.is_dir() %}
      <details class="awdur-directory"><summary>{{ item.name }}</summary>
        <div class="awdur-directory-contents">
          {{ render_dir(item) }}
        </div>
      </details>
    {%- else %}
      <details class="awdur-file"><summary>{{ item.name }}</summary>
        <div class="highlight">
          <pre class="code literal-block">{{ highlight_code(item.read_text(), item) }}</pre>
        </div>
      </details>
    {%- endif %}
  {%- endfor %}
{%- endmacro %}

<div class="awdur-project-tree">
  {{ render_dir(repo) }}
</div>
"""


class HtmlExporter:
    """Export projects to a html representation."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def render(self, project: Project):
        # For now reuse the directory exporter, will come up with a better soln 'soon'
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp, project.name)
            exporter = DirectoryExporter(self.logger)
            exporter.export(project, repo)

            self.logger.info("rendering project: %r", str(repo))
            tmpl = Template(HTML_TEMPLATE)
            return tmpl.render(
                repo=repo, highlight_code=highlight_code, iter_dir=iter_dir
            )

    def export(self, project: Project, output: pathlib.Path):
        """Produce a html representation of the project."""


def iter_dir(root: pathlib.Path):
    for item in sorted(root.glob("*"), key=lambda i: (not i.is_dir(), i.name)):
        if item.name == ".fslckout":
            continue

        yield item


def highlight_code(code: str, filename: pathlib.Path) -> str:
    """Highlight the given code, according to the given filename."""

    try:
        lexer = get_lexer_for_filename(filename)
    except ClassNotFound:
        try:
            lexer = guess_lexer(code)
        except ClassNotFound:
            lexer = get_lexer_by_name("text")

    formatter = HtmlFormatter[str](nowrap=True)
    return highlight(code, lexer, formatter)
