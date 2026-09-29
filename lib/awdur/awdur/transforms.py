from __future__ import annotations

import logging
import typing

from docutils import nodes
from docutils.transforms import Transform

from awdur.directives import code_block
from awdur.directives import file
from awdur.directives import project
from awdur.project import Blob
from awdur.project import ProjectManager

if typing.TYPE_CHECKING:
    from awdur.project import ProjectManager


class CodeMetdataVisitor(nodes.SparseNodeVisitor):
    """Walk a doctree and fill in missing metadata fields based on the surrounding
    context."""

    def __init__(
        self,
        *args,
        logger: logging.Logger | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.logger = (logger or logging.getLogger(__name__)).getChild(
            self.__class__.__name__
        )

        # Assume everything is in the default project, unless told otherwise
        self.ctx_stack: list[dict[str, str]] = [
            {"in-project": "default"},
        ]

    @property
    def context(self) -> dict[str, str]:
        """Return a flattened context based on the current stack of contexts."""
        ctx: dict[str, str] = {}
        for vars in self.ctx_stack:
            ctx.update(vars)

        return ctx

    def add_context(self, name: str, value: str):
        """Add a value to the current context"""
        self.ctx_stack[-1][name] = value

    def visit_section(self, node: nodes.section):
        """Each time we enter a section, push an empty context onto the stack"""
        self.ctx_stack.append({})

    def depart_section(self, node: nodes.section):
        """Each time we depart a section, pop a context off the stack"""
        _ = self.ctx_stack.pop()

    def visit_field(self, node: nodes.field):
        """Set the context based on fields."""

        try:
            name, value, *_ = node.children
            self.add_context(name.astext(), value.astext())
        except Exception:
            self.logger.exception("Unable to set context")

    def visit_code_block(self, node: code_block):
        for name, value in self.context.items():
            if name not in node.attributes and name in code_block.user_attributes:
                node.attributes[name] = value

    def visit_project(self, node: project) -> None:
        """Project nodes define their own context scope."""
        self.ctx_stack.append({"in-project": node["name"]})

    def depart_project(self, node: project):
        _ = self.ctx_stack.pop()

    def visit_file(self, node: file) -> None:
        """File nodes define their own context scope."""

        # First apply the current content
        for name, value in self.context.items():
            if name not in node.attributes and name in file.user_attributes:
                node.attributes[name] = value

        # Then push the a new context defined by the file.
        self.ctx_stack.append({**node.attributes})

    def depart_file(self, node: file):
        _ = self.ctx_stack.pop()


class ResolveProjectMetadataTransform(Transform):
    """A transform for resolving and inlining metadata relevant to projects."""

    default_priority = 500

    def apply(self):
        visitor = CodeMetdataVisitor(self.document)
        _ = self.document.walk(visitor)


class UpdateProjectTransform(Transform):
    """A transform that walks all codeblocks and updates the project state."""

    default_priority = ResolveProjectMetadataTransform.default_priority + 1

    def apply(self):
        manager: ProjectManager = self.document.settings.awdur_project_manager

        # Not sure why this is not set on the document itself...
        filename = self.document.reporter.source
        src = self.document.rawsource
        srcblob = Blob.create(src, -1)

        if manager.get_blob(uuid=srcblob.uuid) is not None:
            manager.logger.debug("Source file %r up to date, nothing to do.", filename)
            return

        if not manager.updating:
            manager.start_update(f"Updated {filename}")

        _ = manager.add_src(src, filename)

        self.update_files(manager)
        self.update_codeblocks(manager)

        # Be sure to commit changes!
        # TODO: Probably need to rethink this in the Sphinx use case.
        manager.commit_update()

    def update_files(self, manager: ProjectManager):
        """Update based on all the file nodes in the document."""

        for node in self.document.findall(file):
            filename = node["filename"]

            if (project_name := node.attributes.get("in-project")) is None:
                manager.logger.warning(
                    "skipping file: %r, not part of any project: %r",
                    filename,
                    node.source,
                )
                continue

            _ = manager.set_file_properties(
                filename, project_name, template=node.attributes.get("use-template")
            )

    def update_codeblocks(self, manager: ProjectManager):
        """Update based on all the code blocks in the document."""
        for node in self.document.findall(code_block):
            if (project_name := node.attributes.get("in-project")) is None:
                manager.logger.debug(
                    "skipping code block, not part of any project\n%s", node.astext()
                )
                continue

            code = node.astext()

            match node.attributes.get("kind"):
                case "code":
                    if (filename := node.attributes.get("in-file")) is not None:
                        _ = manager.add_fragment(
                            code,
                            filename=filename,
                            project=project_name,
                            slot=node.attributes.get("in-slot", "content"),
                            revision=node.attributes.get("at-revision", "1"),
                        )

                case "template":
                    name = node.attributes["name"]
                    _ = manager.add_template(name, code, project_name)

                case _:
                    manager.logger.warning(
                        "skipping code block, unknown kind %r\n%s", code
                    )


class RenderProjectTransform(Transform):
    """Transform that converts ``project`` and ``file`` nodes into an something
    that normal writers can process."""

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

        # html = HtmlExporter(logger=manager.logger)

        for node in self.document.findall(condition=file):
            parent = node.parent
            idx = parent.children.index(node)
            parent.children.remove(node)

        for node in self.document.findall(condition=project):
            # project_name = node["name"]
            # project: ProjectManager = manager[project_name]

            # content = html.render(project)
            # tree = nodes.raw("", content, format="html")

            parent = node.parent
            idx = parent.children.index(node)
            parent.children.remove(node)

            # parent.children.insert(idx, tree)
