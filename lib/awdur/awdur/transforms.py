from __future__ import annotations

import contextlib
import typing

from docutils import nodes
from docutils.transforms import Transform

from awdur.directives import code_block
from awdur.directives import project_tree
from awdur.project import Blob
from awdur.project import HtmlExporter
from awdur.project import ProjectManager

if typing.TYPE_CHECKING:
    from awdur.project import ProjectManager


class CodeMetdataVisitor(nodes.SparseNodeVisitor):
    """Walk a doctree and fill in missing metadata fields based on the surrounding
    context."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context: dict[str, str] = {}
        self.found_projects: set[str] = set()

    def visit_docinfo(self, node: nodes.docinfo):
        """Set the context based on docinfo fields."""

        for field in node:
            with contextlib.suppress(IndexError):
                name = field[0].astext()
                value = field[1].astext()

                self.context[name] = value

    def visit_field_list(self, node: nodes.field_list):
        """Set the context based on the current field list."""
        for field in node:
            with contextlib.suppress(IndexError):
                name = field[0].astext()
                value = field[1].astext()

                self.context[name] = value

    def visit_code_block(self, node: code_block):
        for name, value in self.context.items():
            if name not in node.attributes and name in code_block.user_attributes:
                node.attributes[name] = value

        project = node.attributes.get("project")

        # TODO: make this configurable
        if project is None:
            project = "default"
            node.attributes["project"] = project

        # Note the project name
        self.found_projects.add(project)

    def visit_project_tree(self, node: project_tree) -> None:
        pass


class ResolveProjectMetadataTransform(Transform):
    """A transform for resolving and inlining metadata relevant to projects."""

    default_priority = 500

    def apply(self):
        visitor = CodeMetdataVisitor(self.document)
        _ = self.document.walk(visitor)
        self.document.attributes["projects"] = visitor.found_projects


class UpdateProjectTransform(Transform):
    """A transform that walks all codeblocks and updates the project state."""

    default_priority = ResolveProjectMetadataTransform.default_priority + 1

    def apply(self):
        manager: ProjectManager = self.document.settings.awdur_project_manager

        # Not sure why this is not set on the document itself...
        filename = self.document.reporter.source
        src = self.document.rawsource
        srcblob = Blob.create(src, -1)

        if manager.get_blob(srcblob.uuid) is not None:
            manager.logger.debug("Source file %r up to date, nothing to do.", filename)
            return

        # TODO: need to rethink this for the Sphinx use case.
        if not manager.updating:
            manager.start_update(f"Updated {filename}")

        _ = manager.add_src(src, filename)

        for node in self.document.findall(code_block):
            if (project_name := node.attributes.get("project")) is None:
                manager.logger.debug(
                    "skipping code block, not part of any project\n%s", node.astext()
                )
                continue

            code = node.astext()

            match node.attributes.get("kind"):
                case "code":
                    _ = manager.add_fragment(
                        code,
                        filename=node.attributes.get("filename", "<<default>>"),
                        project=project_name,
                        slot=node.attributes.get("slot", "content"),
                        revision=node.attributes.get("revision", "1"),
                    )

                case "template":
                    name = node.attributes["name"]
                    _ = manager.add_template(name, code, project_name)

                case _:
                    manager.logger.warning(
                        "skipping code block, unknown kind %r\n%s", code
                    )

        # Be sure to commit changes!
        # TODO: Probably need to rethink this in the Sphinx use case.
        manager.commit_update()


class ProjectBrowserTransform(Transform):
    """Transform that converts the ``project_tree`` node into an actual project tree."""

    default_priority = UpdateProjectTransform.default_priority + 1

    def apply(self):
        try:
            manager: ProjectManager = self.document.settings.awdur_project_manager
        except AttributeError:
            # When registered as a post transform in Sphinx, there's no guarantee that
            # every document will have the `awdur_project_manager` set.
            #
            # In that scenario it makes sense to bail, however we will have to see how
            # masty it makes debugging issues in the future.
            return

        html = HtmlExporter(logger=manager.logger)

        for node in self.document.findall(condition=project_tree):
            project_name = node["name"]
            project: ProjectManager = manager[project_name]

            content = html.render(project)
            tree = nodes.raw("", content, format="html")

            parent = node.parent
            idx = parent.children.index(node)
            parent.children.remove(node)

            parent.children.insert(idx, tree)
