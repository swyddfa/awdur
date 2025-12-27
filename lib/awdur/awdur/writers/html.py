from __future__ import annotations

from docutils.transforms import Transform
from docutils.writers.html5_polyglot import Writer


class HTMLWriter(Writer):
    """An awdur secific html writer."""

    def get_transforms(self) -> list[type[Transform]]:
        return super().get_transforms()
