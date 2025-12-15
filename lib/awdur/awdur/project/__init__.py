from __future__ import annotations

import dataclasses
import typing

from docutils import nodes
from docutils.parsers.rst import Directive

if typing.TYPE_CHECKING:
    import pathlib
    from collections.abc import Generator
    from typing import Any


@dataclasses.dataclass
class Project:
    """An awdur project."""

    default_name: str
    """The default base name to assign to the ``<<default>>`` file."""

    structure: dict[str, Any] = dataclasses.field(default_factory=dict)

    files: set[str] = dataclasses.field(default_factory=set)

    def __len__(self):
        return len(self.files)

    def iter(self):
        """Iterate over the project's structure."""
        dirs = [("", self.structure)]

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

    def iter_files(self) -> Generator[tuple[str, list[str]], Any, Any]:
        """Iterate over all the files in the project."""
        for type_, filename, item in self.iter():
            if type_ != "file":
                continue

            yield filename, item

    def add_fragment(self, code: str, filename: str):
        """Add a code fragment to the project."""

        self.files.add(filename)

        dir_ = self.structure
        *parents, name = filename.split("/")

        for parent in parents:
            dir_ = dir_.setdefault(parent, {})

        dir_.setdefault(name, []).append(code)

    def export(self, output: pathlib.Path):
        """Export the project to the given location."""
        if len(self) == 1:
            self.export_single_file(output)
            return

        self.export_multiple_files(output)

    def export_multiple_files(self, output: pathlib.Path):
        """Export a multi-file project."""
        if output.exists() and not output.is_dir():
            raise ValueError(f"Cannot save multi-file project to file: {output}")

        for filename, parts in self.iter_files():
            outfile = output / filename
            content = construct_file(parts)

            if not outfile.parent.exists():
                outfile.parent.mkdir(parents=True)

            _ = outfile.write_text(content)

    def export_single_file(self, output: pathlib.Path):
        """Export a single file project."""

        (filename, parts) = next(self.iter_files())
        if filename == "<<default>>":
            filename = f"{self.default_name}.py"

        if output.exists() and output.is_dir():
            output = output / filename
        else:
            output = output.with_name(filename)

        content = construct_file(parts)
        _ = output.write_text(content)


def construct_file(parts: list[str]) -> str:
    """Assemble a file out of its consituent parts."""
    content = "\n\n".join(parts)

    # Ensure files have a trailing new line
    if content[-1] != "\n":
        return content + "\n"

    return content


class ProjectBrowser(Directive):
    """A directive that inserts a project file browser into the page."""

    required_arguments = 0

    def run(self):
        return [project_node("", name="default")]


class project_node(nodes.General, nodes.Element):
    pass
