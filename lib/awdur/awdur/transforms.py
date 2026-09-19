from __future__ import annotations

import contextlib
import typing

from docutils import nodes
from docutils.transforms import Transform

from awdur.directives import code_block
from awdur.directives import project_tree
from awdur.project import Blob
from awdur.project import HtmlExporter
from awdur.project import Project

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


class BuildProjectsTransform(Transform):
    """A transform that walks all codeblocks and constructs the project(s) they define."""

    default_priority = ResolveProjectMetadataTransform.default_priority + 1

    def apply(self):
        manager: ProjectManager = self.document.settings.awdur_project_manager
        self.logger = manager.logger.getChild("Updater")

        projects = self.get_projects(manager)
        if len(projects) == 0:
            return

        for node in self.document.findall(code_block):
            if (project_name := node.attributes.get("project")) is None:
                self.logger.debug(
                    "skipping code block, not part of any project\n%s", node.astext()
                )
                continue

            if (project := projects.get(project_name)) is None:
                self.logger.debug(
                    "skipping code block, project up to date or disabled\n%s",
                    node.astext(),
                )
                continue

            code = node.astext()

            match node.attributes.get("kind"):
                case "code":
                    _ = project.add_fragment(
                        code,
                        filename=node.attributes.get("filename", "<<default>>"),
                        template=node.attributes.get("template", None),
                        slot=node.attributes.get("slot", "content"),
                    )

                case "template":
                    name = node.attributes["name"]
                    project.add_template(name, code)

                case _:
                    self.logger.warning(
                        "skipping code block, unknown kind %r\n%s", code
                    )

        # Be sure to commit changes to the projects!
        # TODO: Probably need to rethink this in the Sphinx use case.
        for project in projects.values():
            project.commit_update()

    def get_projects(self, manager: ProjectManager) -> dict[str, Project]:
        """Return the projects to be processed."""

        # Get the projects referenced by this document.
        project_names = self.document.attributes["projects"]
        projects = {p: manager[p] for p in project_names}

        if len(projects) == 0:
            # Nothing to do.
            return {}

        # Not sure why this is not set on the document itself...
        filename = self.document.reporter.source
        src = self.document.rawsource
        srcblob = Blob.create(src, -1)

        stale_projects: dict[str, Project] = {}
        for project in projects.values():
            # Has the project already seen this version of the file?
            if project.get_blob(srcblob.uuid) is not None:
                self.logger.debug("project %r up to date, skipping", project.name)
                continue

            # TODO: need to rethink this for the Sphinx use case.
            project.start_update(f"Updated {filename}")
            _ = project.add_src(filename, src)
            stale_projects[project.name] = project

        return stale_projects


class ProjectBrowserTransform(Transform):
    """Transform that converts the ``project_tree`` node into an actual project tree."""

    default_priority = BuildProjectsTransform.default_priority + 1

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
            project: Project = manager[project_name]

            content = html.render(project)
            tree = nodes.raw("", content, format="html")

            parent = node.parent
            idx = parent.children.index(node)
            parent.children.remove(node)

            parent.children.insert(idx, tree)
