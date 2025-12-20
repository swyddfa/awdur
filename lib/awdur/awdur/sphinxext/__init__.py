from __future__ import annotations

import importlib.resources
import pathlib
import typing

from sphinx.directives.code import CodeBlock

from awdur import __version__
from awdur.directives import define_codeblock
from awdur.directives import define_template

from .builder import AwdurBuilder
from .domain import AwdurDomain

if typing.TYPE_CHECKING:
    from sphinx.application import Sphinx


def inject_css(app: Sphinx):
    """Add our  CSS to the build."""

    if "html" not in app.builder.name:
        return

    resources = importlib.resources.files("awdur.sphinxext").joinpath("_static")
    app.config.html_static_path.append(str(resources))

    style_name = "awdur-styles.css"
    app.add_css_file(style_name)


def setup(app: Sphinx):
    codeblock = define_codeblock(CodeBlock)

    app.add_directive("code", codeblock, override=True)
    app.add_directive("code-block", codeblock, override=True)
    app.add_directive("sourcecode", codeblock, override=True)

    AwdurDomain.directives["template"] = define_template(CodeBlock)

    app.add_domain(AwdurDomain)
    app.add_builder(AwdurBuilder)

    _ = app.connect("builder-inited", inject_css)

    return {"version": __version__, "parallel_read_safe": True}
