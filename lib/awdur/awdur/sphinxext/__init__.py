from __future__ import annotations

import importlib.resources
import typing

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.directives.code import CodeBlock
from sphinx.jinja2glue import SphinxFileSystemLoader

from awdur import __version__
from awdur.directives import code_block
from awdur.directives import define_codeblock
from awdur.directives import define_template
from awdur.directives import project_tree
from awdur.project import ProjectManager
from awdur.transforms import BuildProjectsTransform
from awdur.transforms import ProjectBrowserTransform
from awdur.transforms import ResolveProjectMetadataTransform

from .builder import AwdurBuilder
from .domain import AwdurDomain

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

    from awdur.project import Project


def env_get_outdated(
    app: Sphinx,
    env: BuildEnvironment,
    added: set[str],
    changed: set[str],
    removed: set[str],
) -> Sequence[str]:
    """Setup the project instance to use."""
    env.settings["awdur_project_manager"] = ProjectManager(
        default_name=app.config.root_doc
    )

    return set()


def inject_resources(app: Sphinx):
    """Add our CSS and HTML templates to the build."""

    if not isinstance(app.builder, StandaloneHTMLBuilder):
        return

    app.builder.templates.loaders.append(
        SphinxFileSystemLoader(importlib.resources.files("awdur").joinpath("templates"))
    )

    resources = importlib.resources.files("awdur.sphinxext").joinpath("_static")
    app.config.html_static_path.append(str(resources))

    style_name = "awdur-styles.css"
    app.add_css_file(style_name)


def inject_generated_files(app: Sphinx, exc: Exception | None):
    """Allows users to inject additional files into the build by defining a project called
    ``sphinx:<builder_name>``."""
    if exc is not None:
        # abort as an error occurred during the build
        return

    builder = app.builder

    # Look for a project that corresponds to the builder name.
    project_name = f"sphinx:{builder.name}"
    manager: ProjectManager = app.env.settings["awdur_project_manager"]

    if project_name not in manager:
        return

    project: Project = manager[project_name]
    project.export(output=builder.outdir)


def no_op(self, node): ...


def visit_code_block(self, node: code_block):
    header = self.builder.templates.render(
        "awdur/codeblock-header.html", {**node.attributes}
    )
    self.body.append('<div class="awdur-codeblock">')
    self.body.append(header)


def depart_code_block(self, node):
    self.body.append("</div>")


def setup(app: Sphinx):
    # Register custom nodes
    app.add_node(project_tree, html=(no_op, no_op))
    app.add_node(code_block, html=(visit_code_block, depart_code_block))

    # Register custom directives
    codeblock = define_codeblock(CodeBlock)

    app.add_directive("code", codeblock, override=True)
    app.add_directive("code-block", codeblock, override=True)
    app.add_directive("sourcecode", codeblock, override=True)

    # Register custom domain
    AwdurDomain.directives["template"] = define_template(CodeBlock)
    app.add_domain(AwdurDomain)
    app.add_builder(AwdurBuilder)

    # Register custom event handlers
    _ = app.connect("builder-inited", inject_resources)
    _ = app.connect("env-get-outdated", env_get_outdated)
    _ = app.connect("build-finished", inject_generated_files)

    # Register custom transforms
    app.add_transform(ResolveProjectMetadataTransform)
    app.add_transform(BuildProjectsTransform)
    app.add_post_transform(ProjectBrowserTransform)

    return {"version": __version__, "parallel_read_safe": True}
