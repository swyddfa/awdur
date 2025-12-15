from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

try:
    import sphinx

    SPHINX_AVAILABLE = True
except ImportError:
    SPHINX_AVAILABLE = False


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_hello_world_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our hello-world example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-C",
        "-b", "singlehtml",
        "-D", "root_doc=hello-world",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_hello_world_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our hello-world example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C",
        "-D", "root_doc=hello-world",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/hello-world.py"
    assert output.exists()

    content = output.read_text()
    assert content == 'print("Hello, World!")\n'
