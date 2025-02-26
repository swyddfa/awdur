from __future__ import annotations

import pathlib

import pytest
from sphinx.application import Sphinx

WORKSPACES = pathlib.Path(__file__).parent / "workspaces"


@pytest.mark.parametrize(
    "project,expected",
    [
        (
            "simple",
            {
                pathlib.Path("hello.py"): 'print("Hello, World!")\n',
                pathlib.Path("multi_source.py"): (
                    'print("One")\n\n' 'print("Two")\n\n' 'print("Three")\n'
                ),
                pathlib.Path("sequence.py"): (
                    'print("One")\n\n' 'print("Two")\n\n' 'print("Three")\n'
                ),
            },
        )
    ],
)
def test_build_sources(
    project: str, expected: dict[pathlib.Path, str], tmp_path: pathlib.Path
):
    """Ensure that we can generate the expected source files from an awdur Sphinx
    project."""

    src = WORKSPACES / project
    build = tmp_path
    args = {
        "confdir": str(src),
        "srcdir": str(src),
        "outdir": str(build),
        "doctreedir": str(build / ".doctrees"),
        "buildername": "sources",
    }

    app = Sphinx(**args)
    app.build()

    for path, contents in expected.items():
        assert (build / path).read_text() == contents
