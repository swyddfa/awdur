from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
def test_bind_hello_world(workspace: pathlib.Path):
    """Ensure we can generate a html file from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "render", "hello-world.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "hello-world.html"
    assert output.exists()

    text = output.read_text()
    assert "<!DOCTYPE html>" in text
