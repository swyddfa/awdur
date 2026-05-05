from __future__ import annotations

import functools
import pathlib
import typing

from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import TemplateNotFound

if typing.TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any


DEFAULT_TEMPLATE = """\
{%- block header %}{%- endblock %}
{%- block content %}{{ "\n\n".join(content) }}{%- endblock %}
{%- block footer %}{%- endblock %}

"""

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
      <pre class="code literal-block"><code>
{{ render_file(path, item) | trim|e }}
</code></pre>
    </details>
  {%- endif %}
{%- endfor %}
</div>
"""


class ProjectFile:
    """Represents a file within a project."""

    def __init__(
        self, template: str = "default", slots: dict[str, list[str]] | None = None
    ):
        self.template: str = template
        self.slots: dict[str, list[str]] = slots or {}

    def add_fragment(self, slot: str, code: str):
        self.slots.setdefault(slot, []).append(code)


class TemplateLoader(BaseLoader):
    """Used to 'load' the templates defined by the project."""

    def __init__(self):
        self.templates: dict[str, str] = {
            "default": DEFAULT_TEMPLATE,
            "awdur:project_tree": HTML_TEMPLATE,
        }

    def add_template(self, name: str, code: str):
        self.templates[name] = code

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, None, None]:
        if (source := self.templates.get(template, None)) is None:
            raise TemplateNotFound(template)

        return (source, None, None)


class ProjectManager:
    """Manages multiple Project instances."""

    def __init__(self, *, default_name: str = "out"):
        self.default_name: str = default_name
        self.projects: dict[str, Project] = {}

    def __contains__(self, key: str):
        return key in self.projects

    def __getitem__(self, key: str):
        if key not in self.projects:
            self.projects[key] = Project(default_name=self.default_name)

        return self.projects[key]


class Project:
    """An awdur project."""

    def __init__(self, *, default_name: str = "out"):
        self.default_name: str = default_name
        """The name to assign to the ``<<default>>`` filename"""

        self.files: dict[str, Any] = {}
        """Represents the file hierarchy of the project"""

        self.templates: TemplateLoader = TemplateLoader()
        """The set  of templates defined in the project"""

    def __len__(self):
        return len(list(self.iter_files()))

    def iter(self):
        """Iterate over the project's structure."""
        yield from self._iter_dir(self.files)

    def _iter_dir(self, directory: dict[str, Any], parent: str = ""):
        def sort_order(name: str):
            item = directory[name]
            if isinstance(item, dict):
                return (0, name)

            return (1, name)

        for key in sorted(directory.keys(), key=sort_order):
            item = directory[key]
            fullname = pathlib.Path(parent, key)

            if isinstance(item, dict):
                yield "directory", fullname, item
                yield "enter_dir", fullname, None
                yield from self._iter_dir(item, str(fullname))
                yield "exit_dir", fullname, None

            else:
                yield "file", fullname, item

    def iter_files(self) -> Generator[tuple[pathlib.Path, ProjectFile], Any, Any]:
        """Iterate over all the files in the project."""
        for type_, filename, item in self.iter():
            if type_ != "file":
                continue

            yield filename, item

    def add_fragment(self, code: str, filename: str, template: str | None = None):
        """Add a code fragment to the project."""

        dir_ = self.files
        *parents, name = filename.split("/")

        for parent in parents:
            dir_ = dir_.setdefault(parent, {})

        file = dir_.setdefault(name, ProjectFile())
        file.add_fragment("content", code)

        if template is not None:
            file.template = template

    def add_template(self, name: str, code: str):
        """Define a new code template"""
        self.templates.add_template(name, code)

    def render_html(self):
        """Produce a html representation of the project."""
        env = Environment(loader=self.templates)
        template = env.get_template("awdur:project_tree")
        return template.render(
            # TODO: have render_file also apply syntax highlighting.
            project=self,
            render_file=functools.partial(render_file, env),
        )

    def export(self, output: pathlib.Path):
        """Export the project to the given location."""

        env = Environment(loader=self.templates)
        if len(self) == 1:
            self.export_single_file(env, output)
            return

        self.export_multiple_files(env, output)

    def export_multiple_files(self, env: Environment, output: pathlib.Path):
        """Export a multi-file project."""
        if output.exists() and not output.is_dir():
            raise ValueError(f"Cannot save multi-file project to file: {output}")

        for filename, file in self.iter_files():
            # The default file is not exported in multi-file projects
            if filename.name == "<<default>>":
                continue

            outfile = output / filename
            content = render_file(env, filename=outfile, file=file)

            if not outfile.parent.exists():
                outfile.parent.mkdir(parents=True)

            _ = outfile.write_text(content)

    def export_single_file(self, env: Environment, output: pathlib.Path):
        """Export a single file project."""

        (filename, file) = next(self.iter_files())
        if filename.name == "<<default>>":
            filename = pathlib.Path(f"{self.default_name}.py")

        if output.exists() and output.is_dir():
            output = output / filename
        else:
            output = output.with_name(filename.name)

        content = render_file(env, filename=output, file=file)

        if not output.parent.exists():
            output.parent.mkdir(parents=True)

        _ = output.write_text(content)


def render_file(env: Environment, filename: pathlib.Path, file: ProjectFile) -> str:
    """Render a file to plain text"""
    context = {
        "path": filename,
        **file.slots,
    }

    template = env.get_template(file.template)
    return template.render(**context)
