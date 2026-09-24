"""Manages the construction and representation of awdur project databases.

Awdur's project representation is built on top of the fossil file format.

.. seealso::

   `src/schema.c <https://fossil-scm.org/home/file?name=src%2Fschema.c>`__
      The code defining the structure of the database

   `Fossil File Format <https://fossil-scm.org/home/doc/trunk/www/fileformat.wiki>`__
      Defines the structure of each of the main db records, manifest, tickets, etc.

   `Fossil is not Relational <https://fossil-scm.org/home/doc/trunk/www/fossil-is-not-relational.md>`__
      Notes on the overall data model.

"""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import os
import pathlib
import sqlite3
import subprocess
import textwrap
import typing
import uuid
from contextlib import contextmanager

from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import Template
from jinja2 import TemplateNotFound

from .db import Blob
from .db import Config
from .db import Event
from .db import Manifest
from .db import Rcvfrom
from .db import Tag
from .db import User

if typing.TYPE_CHECKING:
    from typing import Any

    from .export import ProjectExporter

UTC = dt.timezone.utc

SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"


class ProjectManager:
    """Manages awdur code projects."""

    def __init__(
        self,
        *,
        cache_dir: pathlib.Path | None = None,
        logger: logging.Logger | None = None,
        username: str | None = None,
    ):
        self.logger: logging.Logger = (logger or logging.getLogger(__name__)).getChild(
            self.__class__.__name__
        )
        """The logger instance to use."""

        self.manifest: Manifest | None = None
        """If set, signals that the project has started an update transaction."""

        self.rcvfrom: Rcvfrom | None = None
        """If set, indicated the current "transaction" in progress."""

        self.dbpath: pathlib.Path = (
            cache_dir or pathlib.Path(".").resolve()
        ) / f"awdur.fossil"
        """The path to the awdur database."""

        self.db: sqlite3.Connection | None = None
        """The connection to the database, if it's currenly open."""

        self.user: User = self._init_db(username or os.environ.get("USER", "awdur"))
        """The user account to use."""

    def _init_db(self, username: str) -> User:
        """Initialize the db if needed and return the user's account record."""

        existing_db = self.dbpath.exists()
        self.logger.debug("Connecting to %r", self.dbpath.as_uri())
        db = sqlite3.connect(self.dbpath)

        if existing_db:
            # TODO: Validate db structure.
            pass
        else:
            _ = db.executescript(SCHEMA.read_text())

            for conf in [
                Config("aux-schema", "2015-01-24"),
                Config("content-schema", "2"),
                Config("hash-policy", "2"),
                Config("project-code", gen_project_code()),
                Config("server-code", value=gen_server_code()),
            ]:
                _ = conf.insert(db)

            db.commit()

        if (user := User.find(db, login=username)) is None:
            user = User(
                username,
                cap="s",
                info=username,
                mtime=dt.datetime.now(tz=UTC),
            ).insert(db)
            db.commit()

        # Release the connection
        db.close()
        return user

    @contextmanager
    def dbcon(self):
        """A context manager for accessing the database connection.

        If we currently have a long-lived connection (i.e. self.db is set) use that.
        Otherwise create an ad-hoc connection that only lives as long as the context
        manager.
        """
        if self.db is None:
            self.logger.debug("Connecting to %r", self.dbpath.as_uri())
            db = sqlite3.connect(self.dbpath)

            yield db

            self.logger.debug("Closing connection to %r", self.dbpath.as_uri())
            db.close()
        else:
            yield self.db

    @property
    def updating(self) -> bool:
        return self.manifest is not None and self.rcvfrom is not None

    def add_src(self, src: str, filename: str) -> Blob | None:
        """Add a src file.

        Parameters
        ----------
        src
           The source to be added

        filename
           The path containing the source.
        """
        fpath = f"src/{filename}"
        return self._add_blob(fpath, src)

    def add_fragment(
        self,
        code: str,
        filename: str,
        project: str,
        revision: str = "1",
        index: int = -1,
        slot: str = "content",
    ):
        """Add a code fragment to a project.

        Parameters
        ----------
        code
           The code fragment itself.

        filename
           The filename within the project to associate the fragment with.

        project
           The project's name.

        revision
           The revision to associate the fragment with.

        slot
           The slot to associate the fragment with.

        index
           The index at which the fragment should be inserted
        """
        if self.manifest is None:
            raise RuntimeError("Unable to add code fragment, update not in progress")

        prefix = f"project/{project}/file/{filename}/{slot}/{revision}/"
        if index == -1:
            # Look at existing files to see what slot index we should use
            idx = len([f for f in self.manifest.files if f.startswith(prefix)])
        else:
            # TODO: Validate index is not taken.
            idx = index

        fpath = f"{prefix}{idx}"
        return self._add_blob(fpath, code)

    def add_template(self, name: str, content: str, project: str):
        """Define a new code template for a project.

        Parameters
        ----------
        name
           The name of the template

        code
           The content of the template

        project
           The project's name.
        """
        fpath = f"project/{project}/template/{name}"
        return self._add_blob(fpath, content)

    def get_blob(self, uuid: str) -> Blob | None:
        """Return the blob with the given uuid, if known"""
        if self.db is None:
            db = sqlite3.connect(self.dbpath)
        else:
            db = self.db

        blob = Blob.find(db, uuid=uuid)

        if self.db is None:
            db.close()

        return blob

    def _add_blob(self, fpath: str, content: str):
        """Add the given blob to the project"""
        if self.manifest is None or self.rcvfrom is None or self.db is None:
            raise RuntimeError("Unable to add blob to project, update not in progress")

        blob = Blob.create(content, self.rcvfrom.rcvid)

        # we may have already recorded this blob
        if (existing := Blob.find(self.db, uuid=blob.uuid)) is not None:
            self.logger.debug("F %s %r, up to date.", fpath, existing)
            return

        updated = blob.insert(self.db)
        self.logger.debug("F %s %r, updated.", fpath, updated)

        self.manifest.add_file(pathlib.Path(fpath), blob)
        return updated

    def start_update(self, comment: str, date: dt.datetime | None = None):
        """Start a new project update."""

        if self.manifest is not None or self.rcvfrom is not None:
            self.abort_update()
            raise RuntimeError(
                "Unable to start project update, update already in progress"
            )

        if self.db is None:
            self.logger.debug("Connecting to %r", self.dbpath.as_uri())
            self.db = sqlite3.connect(self.dbpath)

        now = date or dt.datetime.now(tz=UTC)

        # Create the manifest
        # TODO: This cannot work now that we're rendering projects into the same db!
        if (event := Event.find_latest(self.db)) is None:
            self.manifest = Manifest(
                comment=comment,
                date=now,
                user=self.user.login,
                tags=[
                    Tag("*", "branch", "*", "trunk"),
                    Tag("*", "sym-trunk", "*"),
                ],
            )
            self.logger.debug("Starting first update")
        else:
            if (mblob := Blob.find(self.db, rid=event.objid)) is None:
                raise RuntimeError(f"Unable to load manifest blob rid={event.objid}")

            previous = Manifest.fromblob(mblob)
            self.manifest = previous.make_update(
                comment=comment, date=now, user=self.user.login
            )

            self.logger.debug("Starting update to %r", previous)

        # Create the recvfrom
        self.rcvfrom = Rcvfrom.create(self.user.uid, mtime=now).insert(self.db)
        self.logger.debug("rcvid=%s", self.rcvfrom.rcvid)
        return

    def abort_update(self):
        """Abort the update."""
        self.logger.debug("Aborting update")

        if self.db is not None:
            self.db.rollback()
            self.db.close()
            self.db = None

        self.manifest = None
        self.rcvfrom = None

    def commit_update(self):
        """Commit changes to the db."""

        if self.manifest is None or self.rcvfrom is None:
            self.logger.warning("Commit called outside of an update, rolling back db")
            if self.db is not None:
                self.db.rollback()  # to be safe
                self.db.close()
                self.db = None
            return

        if self.db is None:
            raise RuntimeError("Unable to commit update, no db connection")

        # Add the manifest.
        blob = self.manifest.toblob(self.rcvfrom.rcvid).insert(self.db)
        self.logger.debug("Manifest: %r\n%s", blob, blob.text)

        event = Event(
            "ci",
            self.manifest.date,
            blob.rid,
            self.manifest.user,
            self.manifest.comment.splitlines()[0],
        ).insert(self.db)
        self.logger.debug("%r", event)

        self.db.commit()
        self.db.close()
        self.db = None

        self.manifest = None
        self.rcvfrom = None
        self.logger.debug("Update complete.")

    def export(self, project: str, exporter: ProjectExporter, output: pathlib.Path):
        """Export the given project using the given exporter."""

        if self.manifest is not None or self.rcvfrom is not None:
            raise RuntimeError("Cannot export a project while updating.")

        if self.db is None:
            self.logger.debug("Connecting to %r", self.dbpath.as_uri())
            self.db = sqlite3.connect(self.dbpath)

        if (event := Event.find_latest(self.db)) is None:
            raise RuntimeError("Unable to export project, no project's defined!")

        if (mblob := Blob.find(self.db, rid=event.objid)) is None:
            raise RuntimeError(
                f"Unable to export project, failed to load manifest blob rid={event.objid}"
            )

        manifest = Manifest.fromblob(mblob)
        self.render_project(project, manifest)

        exporter.export(project, self, output)

    def get_project_version(
        self, project: str, revision: str | None = None
    ) -> str | None:
        """Get the uuid of the manifest representing the given project at the given
        revision.

        Parameters
        ----------
        project
           The name of the project

        revision
           The project's revision.
           If ``None``, return the latest revision.
        """
        with self.dbcon() as db:
            cursor = db.execute(
                "SELECT uuid FROM awdur_revisions "
                "WHERE project = ? AND rev LIKE ? "
                "ORDER BY rev DESC LIMIT 1",
                (project, revision or "%"),
            )
            return cursor.fetchone()[0]

    def render_project(self, project: str, manifest: Manifest):
        """Render a project's code from the given manifest."""

        if self.manifest is not None or self.rcvfrom is not None:
            raise RuntimeError("Cannot render a project while updating.")

        if self.db is None:
            self.logger.debug("Connecting to %r", self.dbpath.as_uri())
            self.db = sqlite3.connect(self.dbpath)

        env = Environment(loader=ProjectTemplateLoader(project, manifest, self.db))
        timeline = get_project_timeline(manifest, project)
        self.logger.debug("Timeline: %s", timeline)

        project_manifest: Manifest | None = None

        for rev, fileset in timeline.items():
            self.logger.debug("Exporting revision: %r", rev)
            comment = f"Project export"
            date = dt.datetime.now(tz=UTC)

            if project_manifest is None:
                # first check-in
                project_manifest = Manifest(
                    comment=comment,
                    date=date,
                    user=self.user.login,
                    tags=[
                        Tag("*", "branch", "*", project),
                        Tag("*", f"sym-{project}", "*"),
                        Tag("*", "source", "*", manifest.uuid),
                    ],
                )
            else:
                project_manifest = project_manifest.make_update(
                    comment=comment, date=date, user=self.user.login
                )

            project_manifest.add_tag(Tag("+", "rev", "*", rev))
            rcvfrom = Rcvfrom.create(self.user.uid, mtime=date).insert(self.db)
            for filename, slotblobs in fileset.items():
                context: dict[str, Any] = {
                    "output": {"path": filename},
                    "slots": resolve_file_content(self.db, slotblobs),
                }
                insert_fn = make_code_inserter(context)

                template = env.get_template("default")
                content = template.render(**context, insert=insert_fn)

                blob = Blob.create(content, rcvfrom.rcvid)
                if (existing := Blob.find(self.db, uuid=blob.uuid)) is not None:
                    blob = existing
                    self.logger.debug("F %s %r, existing blob", filename, blob)
                else:
                    blob = blob.insert(self.db)
                    self.logger.debug("F %s, %r, new blob", filename, blob)

                project_manifest.add_file(pathlib.Path(filename), blob)

            # Commit the revision
            blob = project_manifest.toblob(rcvfrom.rcvid).insert(self.db)
            self.logger.debug("Manifest: %r\n%s", blob, blob.text)
            self.db.commit()

        self.db.close()
        self.db = None
        self.rebuild_metadata()

    def rebuild_metadata(self):
        """Call out to fossil to rebuild the metadata tables."""

        # The majority of the fossil db can be derived from the sequence of artifacts.
        # Rather than attempt to keep up with implementation details of the tool, just
        # run the command provided for this purpose
        self.logger.info("Rebuilding metadata...")
        result = subprocess.run(["fossil", "rebuild", "--stats", str(self.dbpath)])


def get_project_timeline(manifest: Manifest, project_name: str):
    """Given a manifest, return the timeline of all files and their revisions"""

    timeline: dict[str, dict[str, dict[str, list[str]]]] = {}
    prefix = f"project/{project_name}/file/"
    for path, uuid in (
        (p.removeprefix(prefix), b.blob.uuid)
        for p, b in manifest.files.items()
        if p.startswith(prefix)
    ):
        *parts, slot, revision, idx = path.split("/")
        filename = "/".join(parts)
        rev = timeline.setdefault(revision, {})

        slots = rev.setdefault(filename, {})
        # TODO: Handle block ordering
        slots.setdefault(slot, []).append(uuid)

    return timeline


def resolve_file_content(db: sqlite3.Connection, slotblobs: dict[str, list[str]]):
    """Resolve all the uuid references in the file's content."""
    slots: dict[str, list[str]] = {}

    for slotname, uuids in slotblobs.items():
        for uuid in uuids:
            if (blob := Blob.find(db, uuid=uuid)) is None:
                raise RuntimeError(f"Unable resolve blob {uuid!r}")

            slots.setdefault(slotname, []).append(blob.text)

    return slots


def make_code_inserter(context):
    """Return the implementation of the 'insert' function to use."""

    def insert(
        lines: list[str], indent: int | str | None = None, indentchar: str = " "
    ) -> str:
        """Insert code into the file."""
        code = "\n\n".join(lines)

        # Treat the code as a template so we can expand nested substitutions
        # - is this a horrible idea??
        t = Template(code)
        code = t.render(**context, insert=insert)

        # Handle indentation
        if isinstance(indent, int):
            indent = indent * indentchar

        if indent:
            code = textwrap.indent(code, indent)

        return code

    return insert


DEFAULT_TEMPLATE = """\
{%- block header %}{%- endblock %}
{%- block content %}{{ insert(slots.content) }}{%- endblock %}
{%- block footer %}
{%- endblock %}
"""


class ProjectTemplateLoader(BaseLoader):
    """Used to load the templates defined by awdur projects."""

    def __init__(self, project: str, manifest: Manifest, db: sqlite3.Connection):
        self.project = project
        self.manifest = manifest
        self.db = db

        self._templates = {}

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, None, None]:
        # If we've loaded it already, use it
        if template in self._templates:
            return self._templates[template]

        filename = f"project/{self.project}/template/{template}"

        # Look for the blob for the given template
        if (file := self.manifest.files.get(filename)) is None:
            # Provide default fallback template
            if template == "default":
                self._templates[template] = tmpl = (DEFAULT_TEMPLATE, None, None)
                return tmpl

            raise TemplateNotFound(template)

        if (blob := Blob.find(self.db, uuid=file.blob.uuid)) is None:
            raise TemplateNotFound(template)

        self._templates[template] = tmpl = (blob.text, None, None)
        return tmpl


def gen_code_from_uuid():
    # Use uuid4 to get a random data, hash it to get a value compatible with fossil's
    return hashlib.sha3_256(str(uuid.uuid4()).encode()).hexdigest()[:20]


gen_project_code = gen_code_from_uuid
gen_server_code = gen_code_from_uuid
