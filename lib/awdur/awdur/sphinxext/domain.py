from __future__ import annotations

import typing
from collections import defaultdict

from docutils import nodes
from sphinx.domains import Domain
from sphinx.util.docutils import SphinxDirective

from awdur.project import ProjectBrowser

if typing.TYPE_CHECKING:
    from typing import Any

    from docutils.nodes import Element
    from sphinx.addnodes import pending_xref
    from sphinx.builders import Builder
    from sphinx.domains import ObjType
    from sphinx.environment import BuildEnvironment


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
