from __future__ import annotations

import pathlib
import sqlite3
import typing
from datetime import datetime

if typing.TYPE_CHECKING:
    from .project import Project
    from .project import ProjectFile


SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"


class FossilExporter:
    def export(self, project: Project, output: pathlib.Path):
        db = init_db(output)
        db.close()


def init_db(output: pathlib.Path):
    """Initialize the db ready for writing."""
    db = sqlite3.connect(output.with_suffix(".fossil"))
    _ = db.executescript(SCHEMA.read_text())

    now = int(datetime.now().timestamp())
    _ = db.executemany(
        "INSERT INTO config(name,value,mtime) VALUES (?,?,?)",
        [
            ("aux-schema", "2015-01-24", now),
            # TODO: generate a proper code, derived from project so it's stable...
            ("project-code", "12", now),
        ],
    )

    # Without some user accounts ``fossil ui`` will not show anything.
    _ = db.executemany(
        "INSERT INTO user(login,pw,cap,info,mtime,jx) VALUES (?,?,?,?,?,?)",
        [
            # TODO: generate an admin account with default password
            ("anonymous", "", "hz", "Anon", None, "{}"),
            ("nobody", "", "gjorz", "Noobdy", None, "{}"),
            ("developer", "", "ei", "Dev", None, "{}"),
            ("reader", "", "kptw", "Reader", None, "{}"),
        ],
    )

    db.commit()

    return db
