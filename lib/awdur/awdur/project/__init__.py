from __future__ import annotations

import typing

from docutils import nodes
from docutils.parsers.rst import Directive
from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import TemplateNotFound

if typing.TYPE_CHECKING:
    import pathlib
    from collections.abc import Generator
    from typing import Any


DEFAULT_TEMPLATE = """\
{%- block header %}{%- endblock %}
{%- block content %}{{ "\n\n".join(content) }}{%- endblock %}
{%- block footer %}{%- endblock %}

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
        self.templates: dict[str, str] = {"default": DEFAULT_TEMPLATE}

    def add_template(self, name: str, code: str):
        self.templates[name] = code

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, None, None]:
        if (source := self.templates.get(template, None)) is None:
            raise TemplateNotFound(template)

        return (source, None, None)


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
        dirs = [("", self.files)]

        try:
            while dir_ := dirs.pop(0):
                path, items = dir_

                for name, item in items.items():
                    fullname = f"{path}/{name}" if path else name

                    if isinstance(item, dict):
                        # Queue the sub-directory to be iterated over
                        dirs.append((fullname, item))
                        yield "directory", fullname, item
                    else:
                        yield "file", fullname, item

        except IndexError:
            pass

    def iter_files(self) -> Generator[tuple[str, ProjectFile], Any, Any]:
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
            if filename == "<<default>>":
                continue

            outfile = output / filename
            content = render_file(env, filename=outfile, file=file)

            if not outfile.parent.exists():
                outfile.parent.mkdir(parents=True)

            _ = outfile.write_text(content)

    def export_single_file(self, env: Environment, output: pathlib.Path):
        """Export a single file project."""

        (filename, file) = next(self.iter_files())
        if filename == "<<default>>":
            filename = f"{self.default_name}.py"

        if output.exists() and output.is_dir():
            output = output / filename
        else:
            output = output.with_name(filename)

        content = render_file(env, filename=output, file=file)
        _ = output.write_text(content)


def render_file(env: Environment, filename: pathlib.Path, file: ProjectFile) -> str:
    """Render a file to plain text"""
    context = {
        "path": filename,
        **file.slots,
    }

    template = env.get_template(file.template)
    return template.render(**context)


class ProjectBrowser(Directive):
    """A directive that inserts a project file browser into the page."""

    required_arguments = 0

    def run(self):
        return [project_node("", name="default")]


class project_node(nodes.General, nodes.Element):
    pass
