from __future__ import annotations

import importlib.resources
import pathlib

from docutils import io
from docutils.core import Publisher
from docutils.parsers import get_parser_class
from docutils.readers import get_reader_class

from awdur.project import Project
from awdur.writers import HTMLWriter


def render(source: pathlib.Path, output: pathlib.Path | None):
    """Render sources to produce a documentation artifact.

    Parameters
    ----------
    source
       The source file to build.
    """
    reader_cls = get_reader_class("standalone")
    parser_cls = get_parser_class("restructuredtext")
    writer = HTMLWriter()

    publisher = Publisher(
        reader=reader_cls(),
        parser=parser_cls(),
        writer=writer,
        settings=None,
        source_class=io.FileInput,
        destination_class=io.FileOutput,
    )

    # It looks like the easiest way to inject additional stylesheets, rather than replace the defaults
    # is to first let docutils initialize the default settings, then append the extra file(s) to the list
    project = Project(default_name=source.stem)
    publisher.process_programmatic_settings(
        settings_spec=None,
        settings_overrides={"awdur_project": project},
        config_section=None,
    )

    stylesheet = importlib.resources.files("awdur.cli").joinpath("default_styles.css")
    publisher.settings.stylesheet_path.append(str(stylesheet))

    publisher.set_source(source_path=str(source))

    destination = output or source.with_suffix(".html")
    publisher.set_destination(destination_path=str(destination))

    _output = publisher.publish(enable_exit_status=False)

    document = publisher.document
    if document.reporter.max_level >= 3:
        return 1
