from __future__ import annotations

import datetime as dt
import logging
import pathlib
import sqlite3
import typing

from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import TemplateNotFound

from .db import Blob
from .db import Manifest

if typing.TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

UTC = dt.timezone.utc

SCHEMA = pathlib.Path(__file__).parent / "project_schema.sql"

DEFAULT_TEMPLATE = """\
{%- block header %}{%- endblock %}
{%- block content %}{{ insert(slots.content) }}{%- endblock %}
{%- block footer %}
{%- endblock %}
"""


class TemplateLoader(BaseLoader):
    """Used to 'load' the templates defined by the project."""

    def __init__(self):
        self.templates: dict[str, str] = {
            "default": DEFAULT_TEMPLATE,
        }

    def add_template(self, name: str, code: str):
        self.templates[name] = code

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, None, None]:
        if (source := self.templates.get(template, None)) is None:
            raise TemplateNotFound(template)

        return (source, None, None)


class ProjectManager:
    """Manages multiple Project instances."""

    def __init__(
        self, *, default_name: str | None = "out", logger: logging.Logger | None = None
    ):
        self.default_name: str | None = default_name
        self.projects: dict[str, Project] = {}

        parent_logger = logger or logging.getLogger(__name__)
        self.logger: logging.Logger = parent_logger.getChild("Project")

    def __contains__(self, key: str):
        return key in self.projects

    def __getitem__(self, key: str):
        if key not in self.projects:
            self.projects[key] = Project(
                key, default_name=self.default_name, logger=self.logger
            )

        return self.projects[key]


class Project:
    """An awdur project."""

    def __init__(
        self,
        name: str,
        *,
        default_name: str | None = "out",
        logger: logging.Logger | None = None,
    ):
        self.name: str = name
        """The name of the project."""

        self.default_filename = default_name
        """The default filename to use"""

        parent_logger = logger or logging.getLogger(__name__)
        self.logger: logging.Logger = parent_logger.getChild(name)
        """The logger instance to use."""

        self.db: sqlite3.Connection = self._init_db()
        self.rcvid = 1  # probably not needed, but here if we need it.

        self.manifest: Manifest | None = None
        """If set, signals that the project has started an update transaction."""

    def _init_db(self) -> sqlite3.Connection:
        db = sqlite3.connect(f"{self.name}.awdprj")
        _ = db.executescript(SCHEMA.read_text())
        db.commit()

        return db

    def get_blob(self, uuid: str) -> Blob | None:
        """Return the blob with the given id, returns ``None`` if not found."""
        cursor = self.db.execute("SELECT * FROM blob WHERE uuid = ?", (uuid,))
        if (row := cursor.fetchone()) is None:
            return None

        return Blob.fromdb(*row)

    def add_src(self, filename: str, src: str) -> Blob | None:
        """Add a src file to the project."""
        fpath = f"src/{filename}"
        blob = Blob.create(src, self.rcvid)

        # we may have already recorded this blob
        if (existing := self.get_blob(blob.uuid)) is not None:
            self.logger.debug("F %s %r, up to date.", fpath, existing)
            return

        updated = blob.insert(self.db)
        self.logger.debug("F %s %r, updated.", fpath, updated)

        # TODO: update manifest
        return updated

    def add_fragment(
        self,
        code: str,
        filename: str,
        revision: str = "1",
        template: str | None = None,
        slot: str = "content",
    ):
        """Add a code fragment to the project."""

        if filename == "<<default>>":
            if self.default_filename is not None:
                filename = self.default_filename
            else:
                return

        # TODO: Handle multiple blocks per slot.
        idx = 0

        fpath = f"file/{filename}/{slot}/{revision}/{idx}"
        return self._add_blob(fpath, code)

    def add_template(self, name: str, code: str):
        """Define a new code template"""
        fpath = f"template/{name}"
        return self._add_blob(fpath, code)

    def _add_blob(self, fpath: str, content: str):
        """Add the given blob to the project"""
        if self.manifest is None:
            raise RuntimeError("Unable to add blob to project, update not in progress")

        blob = Blob.create(content, self.rcvid)

        # we may have already recorded this blob
        if (existing := self.get_blob(blob.uuid)) is not None:
            self.logger.debug("F %s %r, up to date.", fpath, existing)
            return

        updated = blob.insert(self.db)
        self.logger.debug("F %s %r, updated.", fpath, updated)

        self.manifest.add_file(pathlib.Path(fpath), blob)
        return updated

    def start_update(self, comment: str, date: dt.datetime | None = None):
        """Start a new project update."""
        if self.manifest is not None:
            self.abort_update()
            raise RuntimeError(
                "Unable to start project update, update already in progress"
            )

        self.manifest = Manifest(
            comment=comment,
            date=date or dt.datetime.now(tz=UTC),
            user="awdur",
        )
        self.logger.debug("Starting update...")

    def abort_update(self):
        """Abort the update."""
        self.logger.debug("Aborting update...")
        self.db.rollback()
        self.manifest = None

    def commit_update(self):
        """Commit changes to the db."""

        # Assume no manifest => no changes
        if self.manifest is None:
            self.logger.warning("Commit called without a manifest, rolling back db...")
            self.db.rollback()  # to be safe
            return

        # Add the manifest.
        manifest = self.manifest.build()
        blob = Blob.create(manifest, self.rcvid).insert(self.db)
        self.logger.debug("Manifest: %r\n%s", blob, manifest)

        event = Event(
            "ci",
            self.manifest.date,
            blob.rid,
            self.manifest.user,
            self.manifest.comment.splitlines()[0],
        ).insert(self.db)
        self.logger.debug("Event: %r", event)

        self.db.commit()
        self.manifest = None
        self.logger.debug("Update complete.")


@typing.final
class Event:
    """Represents a record from awdur's ``event`` table."""

    def __init__(
        self, type: str, mtime: dt.datetime, objid: int, uid: str, comment: str
    ):
        self.type = type
        self.mtime = mtime
        self.objid = objid
        self.uid = uid
        self.comment = comment

    def __repr__(self):
        return f"Event<{self.uid}({self.type}); {self.comment}>"

    @classmethod
    def fromdb(cls, type: str, mtime: float, objid: int, uid: str, comment: str):
        return cls(type, dt.datetime.fromtimestamp(mtime), objid, uid, comment)

    def insert(self, db: sqlite3.Connection | sqlite3.Cursor):
        """Insert this record into the given db."""
        cursor = db.execute(
            "INSERT INTO event(type, mtime, objid, uid, comment) VALUES (?,?,?,?,?) RETURNING *",
            (self.type, self.mtime.timestamp(), self.objid, self.uid, self.comment),
        )
        event = Event.fromdb(*cursor.fetchone())
        return event
