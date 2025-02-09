from __future__ import annotations

import dataclasses
import typing
from collections import defaultdict

from docutils import nodes
from sphinx.domains import Domain
from sphinx.util.docutils import SphinxDirective

if typing.TYPE_CHECKING:
    from typing import Any


class ProjectBrowser(SphinxDirective):
    """A directive that inserts a project file browser into the page."""

    required_arguments = 0

    def run(self):
        return [project_node("", name="default")]


@dataclasses.dataclass
class Project:
    """An awdur project."""

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

    def iter_files(self):
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


class project_node(nodes.General, nodes.Element):
    pass


def visit_project_node(self, node):
    name = node["name"]

    self.body.append(f"""\
    <div id="awdur-project-{name}" class="awdur-project-browser">
      <div hx-get="/_awdur/projects/{name}/"
           hx-trigger="load"
           hx-select=".awdur-container"
           hx-target="closest .awdur-project-browser"
           hx-swap="outerHTML">
      </div>
    </div>
    """)


def depart_project_node(self, node): ...


class AwdurDomain(Domain):
    """A domain that serves as a central point for awdur functionality."""

    name = "awdur"
    label = "Awdur"

    object_types: dict[str, ObjType] = {}

    directives = {
        "project-browser": ProjectBrowser,
    }

    roles = {}

    @property
    def projects(self) -> dict[str, Any]:
        return self.data.setdefault("projects", defaultdict(Project))

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Element | None:
        """Resolve cross references"""

        # TODO:
        # if (record := self.records.find(identifier=target)) is None:
        #     return None

        # if record.docname is None:
        #     return None

        # if (linktext := contnode.astext()) == target:
        #     contnode = nodes.Text(record.title)
        # else:
        #     contnode = nodes.Text(linktext)

        # return make_refnode(
        #     builder, fromdocname, record.docname, None, [contnode], record.title
        # )
