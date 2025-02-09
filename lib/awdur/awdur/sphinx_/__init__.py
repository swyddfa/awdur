from __future__ import annotations

import importlib.resources as resources
import pathlib
import typing

from docutils import nodes
from docutils.parsers.rst import directives
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer_for_filename
from sphinx.builders import Builder
from sphinx.directives.code import CodeBlock
from sphinx.jinja2glue import SphinxFileSystemLoader
from sphinx.util.display import status_iterator
from sphinx.util.logging import getLogger

from .domain import (
    AwdurDomain,
    Project,
    depart_project_node,
    project_node,
    visit_project_node,
)

if typing.TYPE_CHECKING:
    from typing import Iterable

    from sphinx.application import Sphinx


DEFAULT_HTMX_URL = "https://unpkg.com/htmx.org@2.0.4"
logger = getLogger("awdur")


class CodeFragment(CodeBlock):
    """A fragment of code that may be included in other places."""

    option_spec = {
        **CodeBlock.option_spec,
        "filename": directives.unchanged,
    }

    def run(self):
        result = super().run()

        if not isinstance(code := result[0], nodes.literal_block):
            print(f"Unable to process {code}")
            return result

        if (filename := self.options.get("filename")) is not None:
            code.attributes["filename"] = filename

            # Add a header to the code block indicating where it is being saved to.
            header = nodes.container(
                "",
                nodes.literal("", filename, classes=["awdur-codeblock-filename"]),
                classes=["awdur-codeblock-header"],
            )
            result.insert(0, header)

            container = nodes.container("", *result, classes=["awdur-codeblock"])
            return [container]

        return result


class SourceCodeBuilder(Builder):
    """Builder that extracts source files from documentation."""

    name = "sources"
    format = "plaintext"

    def init(self):
        """Initialize any resources we require"""

        if not (out := pathlib.Path(self.outdir)).exists():
            out.mkdir(parents=True)

    def get_outdated_docs(self) -> str | Iterable[str]:
        """Return the outdated docs that need to be processed."""
        # For now, return everything
        return self.env.found_docs

    def get_target_uri(self, docname: str, typ: str | None = None) -> str:
        """Return the uri corresponding with the given docname."""
        # TODO: What to do here, as we don't really have any relation between a document
        # and a source code file...
        return f"{docname}.txt"

    def prepare_writing(self, docnames: set[str]) -> None:
        """Prepare to write the given docnames"""

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        """Write the given document to the file system."""

    def finish(self):
        """Actually write all the code to disk"""

        awdur: AwdurDomain = self.env.domains["awdur"]
        project = awdur.projects["default"]

        iter = status_iterator(
            project.iter_files(),
            "writing source files...",
            "brown",
            len(project),
            self.app.verbosity,
            stringify_func=lambda i: i[0],
        )
        for filename, blocks in iter:
            filepath = pathlib.Path(self.outdir, filename)

            if not filepath.parent.exists():
                filepath.parent.mkdir(parents=True)

            filepath.write_text("\n\n".join(blocks))


def discover_code(app: Sphinx, doctree):
    """Discover all the code fragments contained in the given document"""

    awdur: AwdurDomain = app.env.domains["awdur"]

    for code_block in doctree.traverse(nodes.literal_block):
        logger.debug("[awdur] found block: %s", code_block)
        if (filename := code_block.attributes.get("filename", None)) is None:
            logger.debug("[awdur] no file name, skipping")
            continue

        project = awdur.projects["default"]
        project.add_fragment(code_block.rawsource, filename)


def prepare_builder(app: Sphinx):
    if hasattr(builder := app.builder, "add_js_file"):
        # Import HTMX if needed
        if (htmx_url := app.config.awdur_htmx_url) is not None:
            builder.add_js_file(htmx_url)

        # Setup html template path
        builder.templates.loaders.append(
            SphinxFileSystemLoader(resources.files("awdur").joinpath("templates"))
        )


def export_project_files(app: Sphinx):
    """Export the html fragments for any exported project files.

    The pages generated here are the "backend" for the .. awdur:project-files::
    directive.
    """
    awdur: AwdurDomain = app.env.domains["awdur"]
    base = "_awdur/projects"
    project_name = "default"
    project = awdur.projects[project_name]

    root = f"{base}/{project_name}"

    for type_, fullname, item in project.iter():
        docname = f"{root}/{fullname}"
        template = f"awdur/{type_}.html"

        context = {"path": fullname.split("/"), "root": root}

        if type_ == "file":
            code = "\n\n".join(item)
            context["contents"] = render_html_for_project_file(fullname, code)

        else:
            context.update(get_context_for_project_dir(item))

        yield (docname, context, template)

    context = {
        "path": [],
        "root": root,
        **get_context_for_project_dir(project.structure),
    }
    yield (root, context, "awdur/directory.html")


def get_context_for_project_dir(dir_: dict[str, Any]) -> dict[str, Any]:
    """Given a directory from a project, return the corresponding context to use with
    the Jinja template"""

    context = {}
    files: list[str] = []
    dirs: list[str] = []

    for name, item in dir_.items():
        if isinstance(item, dict):
            dirs.append(name)
        else:
            files.append(name)

    context["files"] = sorted(files)
    context["dirs"] = sorted(dirs)

    return context


def render_html_for_project_file(filename: str, code: str):
    """Return the html representing the contents of the given file."""
    try:
        lexer = guess_lexer_for_filename(filename, code)
        formatter = HtmlFormatter(prestyles="margin: 0")
        return highlight(code, lexer, formatter)
    except Exception:
        return f"<pre>{code}</pre>"


def setup(app: Sphinx):
    app.add_config_value(
        "awdur_htmx_url", DEFAULT_HTMX_URL, rebuild="env", types=[str, type(None)]
    )

    app.add_directive("code-block", CodeFragment, override=True)
    app.add_directive("sourcecode", CodeFragment, override=True)

    app.connect("builder-inited", prepare_builder)
    app.connect("doctree-read", discover_code)
    app.connect("html-collect-pages", export_project_files)

    app.add_domain(AwdurDomain)

    app.add_node(project_node, html=(visit_project_node, depart_project_node))

    app.add_builder(SourceCodeBuilder)

    return {"version": "0.1", "parallel_read_safe": True}
