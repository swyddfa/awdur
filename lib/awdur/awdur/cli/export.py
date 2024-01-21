from __future__ import annotations

import pathlib
import sys

from docutils import nodes
from docutils.core import publish_parts
from docutils.transforms import Transform
from docutils.writers import Writer

from ._core import command


class CodeMetdataVisitor(nodes.SparseNodeVisitor):
    """Walk a doctree and fill in missing metadata fields based on the surrounding
    context."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = {}

    def visit_docinfo(self, node: nodes.docinfo):
        """Set the context based on docinfo fields."""

        for field in node:
            name = field[0].astext()
            value = field[1].astext()

            self.context[name] = value

    def visit_field_list(self, node: nodes.field_list):
        """Set the context based on the current field list."""
        for field in node:
            name = field[0].astext()
            value = field[1].astext()

            self.context[name] = value

    def visit_literal_block(self, node: nodes.literal_block):
        """If there is a current context, use it to fill in any missing blanks in the
        code block."""

        for name, value in self.context.items():
            if name not in node.attributes:
                node.attributes[name] = value


class ExtractCodeTransform(Transform):
    """A transform to select only the code blocks defined in a doctree.

    This is also responsible for inlining all the relevant metadata into the
    ``literal_block`` nodes.

    """

    default_priority = 500

    def apply(self):
        # Apply metadata
        visitor = CodeMetdataVisitor(self.document)
        self.document.walk(visitor)

        code_blocks = self.document.findall(nodes.literal_block)
        self.document.children = list(code_blocks)


class SourceCodeWriter(Writer):
    """A writer for writing source code."""

    def get_transforms(self):
        return super().get_transforms() + [ExtractCodeTransform]

    def translate(self):
        all_filenames = set()
        for node in self.document.children:
            filename = node.attributes.get("filename", "<<default>>")
            all_filenames.add(filename)
            self.parts.setdefault(filename, []).append(node.astext())

        for name in all_filenames:
            self.parts[name] = "\n".join(self.parts[name]) + "\n"

        # In the case we produce a single file, set the output also
        if len(all_filenames) == 1:
            self.output = self.parts[list(all_filenames)[0]]


# Document parts that are not source code files.
EXCLUDED_PARTS = {"encoding", "whole", "errors", "version"}


@command
def export(source: pathlib.Path, destination: pathlib.Path):
    """Export source code

    Parameters
    ----------
    source
       The source file to build

    destination
       The location to write to
    """

    project = publish_parts(
        source=source.read_text(),
        source_path=str(source),
        # destination_path="out.html",  # sys.stdout,
        writer=SourceCodeWriter(),
    )

    encoding = project.get("encoding", "utf-8")
    if (content := project.get("whole", None)) is not None:
        # A single file was produced, write that.
        destination.write_text(content, encoding=encoding)
        return

    if (exists := destination.exists()) and not destination.is_dir():
        raise ValueError(f"Cannot write multi-file project to: '{destination}'")
    elif not exists:
        destination.mkdir(parents=True)

    for name, content in project.items():
        if name in EXCLUDED_PARTS:
            continue

        outfile = destination / name

        # Projects may include subfolders.
        if not outfile.parent.exists():
            outfile.parent.mkdir(parents=True)

        outfile.write_text(content, encoding=encoding)
