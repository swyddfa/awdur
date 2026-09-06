from __future__ import annotations

import pathlib
import textwrap
import typing

from jinja2 import Environment
from jinja2 import Template

if typing.TYPE_CHECKING:
    from . import Project
    from . import ProjectFile


class DirectoryExporter:
    """Export a project to files in a directory."""

    def export(self, project: Project, output: pathlib.Path):
        """Export the project to the given location."""

        env = Environment(loader=project.templates)
        if len(project) == 1:
            self.export_single_file(env, project, output)
            return

        self.export_multiple_files(env, project, output)

    def export_multiple_files(
        self, env: Environment, project: Project, output: pathlib.Path
    ):
        """Export a multi-file project."""
        if output.exists() and not output.is_dir():
            raise ValueError(f"Cannot save multi-file project to file: {output}")

        for filename, file in project.iter_files():
            # The default file is not exported in multi-file projects
            if filename.name == "<<default>>":
                continue

            outfile = output / filename
            content = render_file(env, filename=outfile, file=file)

            if not outfile.parent.exists():
                outfile.parent.mkdir(parents=True)

            _ = outfile.write_text(content)

    def export_single_file(
        self, env: Environment, project: Project, output: pathlib.Path
    ):
        """Export a single file project."""

        (filename, file) = next(project.iter_files())
        if filename.name == "<<default>>":
            filename = pathlib.Path(f"{project.default_name}.py")

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
