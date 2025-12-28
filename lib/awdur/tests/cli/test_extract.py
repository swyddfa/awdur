from __future__ import annotations

import os
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


@pytest.mark.parametrize("workspace", ["multiple-blocks"], indirect=True)
def test_extract_multiple_blocks(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "multiple-blocks.rst"], cwd=workspace
    )
    assert result.returncode == 0

    output = workspace / "multiple-blocks.py"
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
def test_extract_multiple_files(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "multiple-files.rst"], cwd=workspace
    )
    assert result.returncode == 0

    # check fib.py
    output = workspace / "multiple-files/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    )

    # check square.py
    output = workspace / "multiple-files/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100"
    )


@pytest.mark.parametrize("workspace", ["inline-templates"], indirect=True)
def test_extract_inline_templates(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "inline-templates.rst"],
        cwd=workspace,
    )
    assert result.returncode == 0

    # check triangle.el
    output = workspace / "inline-templates/triangle.el"
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
    output = workspace / "inline-templates/rectangle.el"
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
def test_extract_project_tree(workspace: pathlib.Path):
    """Ensure we can extract code from the example correctly."""

    result = subprocess.run(
        [sys.executable, "-m", "awdur", "extract", "project-tree.rst"],
        cwd=workspace,
    )
    assert result.returncode == 0

    # check hello.py
    output = workspace / "project-tree/hello.py"
    assert output.exists()

    assert 'print("Hello, World!")\n' == output.read_text()

    # check math/fib.py
    output = workspace / "project-tree/math/fib.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 Fibonacci numbers are: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    )

    # check math/square.py
    output = workspace / "project-tree/math/square.py"
    assert output.exists()

    result = subprocess.run([sys.executable, f"{output}"], capture_output=True)
    assert result.returncode == 0

    stdout = result.stdout.decode("utf-8")
    assert stdout.strip() == (
        "The first 10 square numbers are: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100"
    )

    # check shapes/triangle.py
    output = workspace / "project-tree/shapes/triangle.py"
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
