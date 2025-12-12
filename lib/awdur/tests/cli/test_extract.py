from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
def test_extract_hello_world(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "hello-world.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "hello-world.py"
    assert output.exists()

    assert 'print("Hello, World!")\n' == output.read_text()
