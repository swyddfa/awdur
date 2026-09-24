"""Export a project to a fossil source repo.

"""

from __future__ import annotations

import logging
import os
import pathlib
import sqlite3
import subprocess
import textwrap
import typing
from datetime import datetime
from datetime import timezone

from jinja2 import Environment
from jinja2 import Template

from .db import Blob
from .db import Manifest
from .db import User

UTC = timezone.utc


if typing.TYPE_CHECKING:
    from .manager import ProjectManager


SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"


class FossilExporter:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.username = "awdur"
        self.users = {}


    def init_db(self, dbpath: pathlib.Path) -> tuple[sqlite3.Connection, Blob]:
        """Initialize the db ready for writing.

        Also creates an empty first commit on which the rest of the history can be
        linked to.
        """
        db = sqlite3.connect(dbpath)
        _ = db.executescript(SCHEMA.read_text())

        now = datetime.now(tz=UTC)
        mtime = int(now.timestamp())

        _ = db.executemany(
            "INSERT INTO config(name,value,mtime) VALUES (?,?,?)",
            [
                ("aux-schema", "2015-01-24", mtime),
                ("content-schema", "2", mtime),
                ("hash-policy", "2", mtime),
                # TODO: generate proper codes,
                ("project-code", "12", mtime),
                ("server-code", "34", mtime),
            ],
        )

        # Without some user accounts ``fossil ui`` will not show anything.
        self.users = {
            u.login:
        }
        user = self.users[self.username]

        # Write the blob containing the initial check-in
        manifest = Manifest(
            comment="Initialize project",
            date=now,
            user=user.login,
            logger=self.logger,
        )
        manifest.add_tag("branch", "trunk")
        manifest.add_tag("sym-trunk")

        rcvid = 1
        blob = Blob.create(manifest.build(), rcvid)
        blob = blob.insert(db)

        # Update rcvfrom
        _ = db.execute(
            "INSERT INTO rcvfrom(rcvid,uid,mtime) VALUES (?,?,julianday(?, 'unixepoch'))",
            (1, user.uid, mtime),
        )

        db.commit()
        return db, blob

    def render_file(
        self, env: Environment, filename: pathlib.Path, file: ProjectFile
    ) -> str:
        """Render a file to plain text"""
        context = {
            "output": {"path": filename},
            "slots": file.slots,
        }

        def insert(lines: list[str], indent: int | str | None = None) -> str:
            """Insert code into the file."""
            code = "\n\n".join(lines)

            # Treat the code as a template so we can expand nested substiutions
            # - is this a horrible idea??
            t = Template(code)
            code = t.render(**context, insert=insert)

            # Handle indentation
            if isinstance(indent, int):
                indent = indent * " "

            if indent:
                code = textwrap.indent(code, indent)

            return code

        template = env.get_template(file.template)
        return template.render(**context, insert=insert)
