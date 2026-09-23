"""Export a project to a fossil source repo.

.. seealso::

   `src/schema.c <https://fossil-scm.org/home/file?name=src%2Fschema.c>`__
      The code defining the structure of the database

   `Fossil File Format <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki>`__
      Defines the structure of each of the main db records, manifest, tickets, etc.

   `Fossil is not Relational <https://fossil-scm.org/home/doc/trunk/www/fossil-is-not-relational.md>`__
      Notes on the overall data model.
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

    def export(self, project: ProjectManager, output: pathlib.Path):
        dbpath = output.with_suffix(".fossil")
        if dbpath.exists():
            raise RuntimeError(
                f"File {str(dbpath)!r} already exists and incremental exports are not "
                "supported please delete the existing file or choose another filepath"
            )

        self.logger.info("Initialising database...")
        db, checkin = self.init_db(dbpath)

        self.logger.info("Writing artifacts...")
        env = Environment(loader=project.templates)

        now = datetime.now(tz=UTC)
        user = self.users[self.username]
        manifest = Manifest(
            comment=f"Export files from {project.name}",
            date=now,
            user=user.login,
            previous=[checkin],
        )
        rcvid = 2

        # Update rcvfrom
        _ = db.execute(
            "INSERT INTO rcvfrom(rcvid,uid,mtime) VALUES (?,?,julianday(?, 'unixepoch'))",
            (rcvid, user.uid, now.timestamp()),
        )

        for filename, file in project.iter_files():
            content = self.render_file(env, filename, file)
            blob = Blob.create(content, rcvid).insert(db)
            self.logger.debug("Blob: %s %s %s bytes", blob.uuid, filename, blob.size)
            manifest.add_file(filename, blob)

        blob = Blob.create(manifest.build(), rcvid).insert(db)
        db.commit()
        db.close()

        # The majority of the fossil db can be derived from the sequence of artifacts.
        # Rather than attempt to keep up with implementation details of the tool, just
        # run the command provided for this purpose
        self.logger.info("Rebuilding metadata...")
        result = subprocess.run(
            ["fossil", "rebuild", "--stats", str(dbpath)], capture_output=True
        )
        if result.returncode == 0:
            self.logger.info(result.stdout.decode("utf8"))

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
            u.login: u.insert(db)
            for u in [
                # TODO: generate an admin account with default password
                User(self.username, pw="", cap="s", info=self.username, mtime=now),
                User("anonymous", pw="", cap="hz", info="Anon", mtime=now),
                User("nobody", pw="", cap="gjorz", info="Noobdy", mtime=now),
                User("developer", pw="", cap="ei", info="Dev", mtime=now),
                User("reader", pw="", cap="kptw", info="Reader", mtime=now),
            ]
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
