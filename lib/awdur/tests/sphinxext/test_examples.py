from __future__ import annotations

import os
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
        "-C", "-W",
        "-b", "singlehtml",
        "-D", "root_doc=hello-world",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/hello-world.html"
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["hello-world"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_hello_world_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our hello-world example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C",  "-W",
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


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_blocks_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our multiple-blocks example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C", "-W",
        "-D", "root_doc=multiple-blocks",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-blocks.html"
    assert output.exists()

    content = output.read_text()
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_blocks_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our multiple-blocks example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C", "-W",
        "-D", "root_doc=multiple-blocks",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-blocks.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    # fmt: off
    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        f"A triangle with sides a=3, b=4, c=5 has{os.linesep}"
        f"- Perimeter, P=12{os.linesep}"
        "- Area, A=6.0"
    )
    # fmt: on


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_files_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our multiple-files example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C", "-W",
        "-D", "root_doc=multiple-files",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/multiple-files.html"
    assert output.exists()

    content = output.read_text()
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["multiple-files"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_multiple_files_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our multiple-files example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C", "-W",
        "-D", "root_doc=multiple-files",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    # check fib.py
    output = workspace / "out/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    )

    # check square.py
    output = workspace / "out/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100"
    )


@pytest.mark.parametrize("workspace", ["inline-templates"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_inline_templates_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our inline template example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C", "-W",
        "-D", "root_doc=inline-templates",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/inline-templates.html"
    assert output.exists()

    content = output.read_text()
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["inline-templates"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_inline_templates_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our inline templates example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C", "-W",
        "-D", "root_doc=inline-templates",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    # check triangle.el
    output = workspace / "out/triangle.el"
    assert output.exists()
    assert output.read_text() == (
        ";;; triangle.el --- Description\n"
        "\n"
        "(defun triangle-area (a b c)\n"
        "  (* 0.5 a b))\n"
        "\n"
        "(defun triangle-perimeter (a b c)\n"
        "  (+ a b c))\n"
        "\n"
        "(provide 'triangle)\n"
    )

    # check rectangle.el
    output = workspace / "out/rectangle.el"
    assert output.exists()
    assert output.read_text() == (
        ";;; rectangle.el --- Description\n"
        "\n"
        "(defun rectangle-area (w h)\n"
        "  (* w h))\n"
        "\n"
        "(defun rectangle-perimeter (w h)\n"
        "  (* 2 (+ w h))\n"
        "\n"
        "(provide 'rectangle)\n"
    )


@pytest.mark.parametrize("workspace", ["project-tree"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_project_tree_render(workspace: pathlib.Path):
    """Ensure that we can render docs from our project tree example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "singlehtml",
        "-C", "-W",
        "-D", "root_doc=project-tree",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    output = workspace / "out/project-tree.html"
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


@pytest.mark.parametrize("workspace", ["project-tree"], indirect=True)
@pytest.mark.skipif(not SPHINX_AVAILABLE, reason="test requires sphinx")
def test_project_tree_extract(workspace: pathlib.Path):
    """Ensure that we can extract code from our inline templates example."""

    # fmt: off
    cmd = [
        sys.executable, "-m", "sphinx",
        ".", "out",
        "-b", "awdur",
        "-C", "-W",
        "-D", "root_doc=project-tree",
        "-D", "extensions=awdur.sphinxext",
    ]
    # fmt: on

    result = subprocess.run(cmd, cwd=workspace)
    assert result.returncode == 0

    # check hello.py
    output = workspace / "out/hello.py"
    assert output.exists()

    assert 'print("Hello, World!")\n' == output.read_text()

    # check math/fib.py
    output = workspace / "out/math/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    )

    # check math/square.py
    output = workspace / "out/math/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100"
    )

    # check shapes/triangle.py
    output = workspace / "out/shapes/triangle.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    # fmt: off
    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        f"A triangle with sides a=3, b=4, c=5 has{os.linesep}"
        f"- Perimeter, P=12{os.linesep}"
        "- Area, A=6.0"
    )
    # fmt: on
