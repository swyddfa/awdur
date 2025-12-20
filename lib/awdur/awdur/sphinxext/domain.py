from __future__ import annotations

import pathlib
import subprocess
import sys
import typing
from collections import defaultdict

from docutils import nodes
from docutils.parsers.rst import directives
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


class RenderDirective(SphinxDirective):
    """Render a project through the docutils-only side of the library and embed the
    result using an iframe."""

    required_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "width": directives.length_or_percentage_or_unitless,
        "height": directives.length_or_percentage_or_unitless,
    }

    def run(self):
        source = (self.env.app.srcdir / self.arguments[0]).resolve()
        outname = f"_awdur_renders/{source.stem}.html"
        output = self.env.app.outdir / outname

        if not output.parent.exists():
            output.parent.mkdir(parents=True)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "awdur",
                "render",
                f"{source}",
                "-o",
                f"{output}",
            ],
        )
        if result.returncode != 0:
            raise RuntimeError("Unable to render file")

        iframe_attrs = {
            "height": self.options.get("height", "100%"),
            "width": self.options.get("width", "100%"),
            "src": f"/{outname}",
        }
        iframe_attr_str = " ".join([f'{k}="{v}"' for k, v in iframe_attrs.items()])

        return [
            nodes.raw(
                "",
                f"<iframe {iframe_attr_str}></iframe>",
                format="html",
            )
        ]


class AwdurDomain(Domain):
    """A domain that serves as a central point for awdur functionality."""

    name = "awdur"
    label = "Awdur"

    object_types: dict[str, ObjType] = {}

    directives = {
        "render": RenderDirective,
        # The following directives are populated dynamically during extension setup.
        #
        # 'template'
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
