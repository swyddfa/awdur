from __future__ import annotations

import pathlib
import typing

from docutils import io
from sphinx.builders import Builder
from sphinx.util.display import status_iterator

from awdur.writers import SourceCodeWriter

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

    from docutils import nodes


class AwdurBuilder(Builder):
    """Builder that extracts source files from documentation."""

    name = "awdur"
    format = "plaintext"

    @property
    def outpath(self) -> pathlib.Path:
        """Not entirely sure if this is needed."""
        return pathlib.Path(self.outdir)

    def init(self):
        """Initialize any resources we require"""

        if not self.outpath.exists():
            self.outpath.mkdir(parents=True)

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
        """'Write' the given document to extract the code."""

    def finish(self):
        """Actually write all the code to disk"""

        project = self.env.settings["awdur_project"]
        project.export(self.outpath)
