from __future__ import annotations

import functools
import pathlib
import textwrap
import typing

from jinja2 import Environment
from jinja2 import Template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

if typing.TYPE_CHECKING:
    from . import Project
    from . import ProjectFile


HTML_TEMPLATE = """\
<div class="awdur-project-tree">
{%- for item_type, path, item in project.iter() %}
  {%- if item_type == "enter_dir" %}
    <details class="awdur-directory"><summary>{{ path.name }}</summary>
      <div class="awdur-directory-contents">
  {%- elif item_type == "exit_dir" %}
    </div></details>
  {%- elif item_type == "file" and path.name != "<<default>>" %}
    <details class="awdur-file"><summary>{{ path.name }}</summary>
      <div class="highlight">
        <pre class="code literal-block">{%- set src = render_file(path, item) | trim -%}{{ highlight_code(src, path) }}</pre>
      </div>
    </details>
  {%- endif %}
{%- endfor %}
</div>
"""


class HtmlExporter:
    """Export projects to a html representation."""

    def render(self, project: Project) -> str:
        """Produce a html representation of the project."""
        env = Environment(loader=project.templates)
        template = env.get_template("awdur:project_tree")
        return template.render(
            project=project,
            render_file=functools.partial(render_file, env),
            highlight_code=highlight_code,
        )

    def export(self, project: Project, output: pathlib.Path):
        raise NotImplementedError("TODO: html export")


def render_file(env: Environment, filename: pathlib.Path, file: ProjectFile) -> str:
    """Render a file to plain text"""
    context = {
        "output": {"path": filename},
        "slots": file.slots,
    }

    def insert(lines: list[str], indent: int | str | None = None) -> str:
        """Insert code into the file."""
        code = "\n\n".join(lines)

        # Treat the code as a template so we can expand nested substiutions
        # - is this a horrible idea??
        t = Template(code)
        code = t.render(**context, insert=insert)

        # Handle indentation
        if isinstance(indent, int):
            indent = indent * " "

        if indent:
            code = textwrap.indent(code, indent)

        return code

    template = env.get_template(file.template)
    return template.render(**context, insert=insert)


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
