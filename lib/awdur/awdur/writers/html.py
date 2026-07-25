from __future__ import annotations

import typing

from docutils.writers.html5_polyglot import HTMLTranslator as Translator
from docutils.writers.html5_polyglot import Writer

from awdur.transforms import BuildProjectsTransform
from awdur.transforms import ProjectBrowserTransform
from awdur.transforms import ResolveProjectMetadataTransform

if typing.TYPE_CHECKING:
    from docutils.transforms import Transform


class HTMLWriter(Writer):
    """An awdur secific html writer."""

    def __init__(self):
        super().__init__()
        self.translator_class = HTMLTranslator

    def get_transforms(self) -> list[type[Transform]]:
        return super().get_transforms() + [
            ResolveProjectMetadataTransform,
            BuildProjectsTransform,
            ProjectBrowserTransform,
        ]


class HTMLTranslator(Translator):
    def visit_code_block(self, node):
        pass

    def depart_code_block(self, node) -> None:
        pass
