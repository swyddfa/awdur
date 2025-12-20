from __future__ import annotations

import typing

from sphinx.directives.code import CodeBlock

from awdur import __version__
from awdur.directives import define_codeblock
from awdur.directives import define_template

from .builder import AwdurBuilder
from .domain import AwdurDomain

if typing.TYPE_CHECKING:
    from sphinx.application import Sphinx


def setup(app: Sphinx):
    codeblock = define_codeblock(CodeBlock)

    app.add_directive("code", codeblock, override=True)
    app.add_directive("code-block", codeblock, override=True)
    app.add_directive("sourcecode", codeblock, override=True)

    AwdurDomain.directives["template"] = define_template(CodeBlock)

    app.add_domain(AwdurDomain)
    app.add_builder(AwdurBuilder)

    return {"version": __version__, "parallel_read_safe": True}
