from __future__ import annotations

import typing

from docutils import nodes
from docutils.transforms import Transform

from awdur.directives import project_tree
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

    def visit_project_tree(self, node: project_tree) -> None:
        pass


class ResolveProjectMetadataTransform(Transform):
    """A transform for resolving and inlining metadata relevant to projects."""

    default_priority = 500

    def apply(self):
        visitor = CodeMetdataVisitor(self.document)
        _ = self.document.walk(visitor)


class BuildProjectsTransform(Transform):
    """A transform that walks all codeblocks and constructs the project(s) they define."""

    default_priority = ResolveProjectMetadataTransform.default_priority + 1

    def apply(self):
        project: Project = self.document.settings.awdur_project

        for node in self.document.findall(nodes.literal_block):
            filename = node.attributes.get("filename", "<<default>>")
            code = node.astext()

            if (kind := node.attributes.get("kind")) == "code":
                template = node.attributes.get("template", None)
                project.add_fragment(code, filename, template=template)

            elif kind == "template":
                name = node.attributes["name"]
                project.add_template(name, code)


class ProjectBrowserTransform(Transform):
    """Transform that converts the ``project_tree`` node into an actual project tree."""

    default_priority = BuildProjectsTransform.default_priority + 1

    def apply(self):
        project: Project = self.document.settings.awdur_project
        content = project.render_html()
        tree = nodes.raw("", content, format="html")

        for node in self.document.findall(condition=project_tree):
            parent = node.parent
            idx = parent.children.index(node)
            parent.children.remove(node)

            parent.children.insert(idx, tree)
