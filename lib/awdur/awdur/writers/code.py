from __future__ import annotations

import typing

from docutils import nodes
from docutils.transforms import Transform
from docutils.writers import Writer

if typing.TYPE_CHECKING:
    from awdur.project import Project


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
        _ = self.document.walk(visitor)


class SourceCodeWriter(Writer):
    """A writer for writing source code."""

    def __init__(self, project: Project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def get_transforms(self):
        return [ExtractCodeTransform]

    def translate(self):
        if self.document is None:
            return

        self.parts["project"] = self.project

        for node in self.document.findall(nodes.literal_block):
            filename = node.attributes.get("filename", "<<default>>")
            code = node.astext()

            if (kind := node.attributes.get("kind")) == "code":
                template = node.attributes.get("template", None)
                self.project.add_fragment(code, filename, template=template)

            elif kind == "template":
                name = node.attributes["name"]
                self.project.add_template(name, code)
