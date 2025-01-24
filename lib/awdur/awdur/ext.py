from __future__ import annotations

import pathlib
import typing

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.builders import Builder
from sphinx.directives.code import CodeBlock
from sphinx.util.display import status_iterator
from sphinx.util.logging import getLogger

from ._version import __version__

if typing.TYPE_CHECKING:
    from typing import Iterable

    from sphinx.application import Sphinx


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
                classes=["awdur-codeblock-header"]
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

        self.files: dict[str, list[str]] = {}

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

        for code_block in doctree.traverse(nodes.literal_block):
            logger.debug("[awdur] found block: %s", code_block)
            if (filename := code_block.attributes.get("filename", None)) is None:
                logger.debug("[awdur] no file name, skipping")
                continue

            self.files.setdefault(filename, []).append(code_block.rawsource)

    def finish(self):
        """Actually write all the code to disk"""
        logger.debug("[awdur] %s", self.files)

        iter = status_iterator(
            self.files,
            "writing source files...",
            "brown",
            len(self.files),
            self.app.verbosity,
            stringify_func=str,
        )
        for filename in iter:
            blocks = self.files[filename]
            filepath = pathlib.Path(self.outdir, filename)

            if not filepath.parent.exists():
                filepath.parent.mkdir(parents=True)

            filepath.write_text("\n\n".join(blocks))


def setup(app: Sphinx):
    app.add_directive("code-block", CodeFragment)
    app.add_directive("sourcecode", CodeFragment)

    app.add_builder(SourceCodeBuilder)

    return {"version": __version__, "parallel_read_safe": True}
