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

import dataclasses
import datetime as dt
import fnmatch
import functools
import getpass
import hashlib
import itertools
import logging
import pathlib
import re
import sqlite3
import subprocess
import textwrap
import typing
import uuid
from collections import defaultdict
from contextlib import contextmanager

from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import Template
from jinja2 import TemplateNotFound

from .db import Artifact
from .db import Blob
from .db import Config
from .db import Manifest
from .db import User
from .manifest import AwdurManifestBuilder
from .manifest import ManifestBuilder

if typing.TYPE_CHECKING:
    from typing import Any

    from .export import ProjectExporter

UTC = dt.timezone.utc

SCHEMA = pathlib.Path(__file__).parent / "fossil_schema.sql"


@dataclasses.dataclass
class RepoStats:
    """Simple datatype to hold the output of the ``fossil rebuild --stats`` command."""

    artifacts: int = dataclasses.field(default=0)
    """Total count of artifacts in the project."""

    manifests: int = dataclasses.field(default=0)
    """Count of manifest records."""

    clusters: int = dataclasses.field(default=0)
    """Count of cluster records."""

    tags: int = dataclasses.field(default=0)
    """Count of tag records."""

    wikis: int = dataclasses.field(default=0)
    """Count of wiki pages."""

    attachments: int = dataclasses.field(default=0)
    """Count of attachments."""

    events: int = dataclasses.field(default=0)
    """Count of events (I *think* an event is a 'tech note' in this context)."""

    other: int = dataclasses.field(default=0)
    """Count of 'other' records (e.g. file blobs)."""


class RepoManager:
    """Manages awdur repositories."""

    def __init__(
        self,
        *,
        data_dir: pathlib.Path | None = None,
        clear_cache: bool = False,
        logger: logging.Logger | None = None,
        username: str | None = None,
    ):
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        """The logger instance to use."""

        self.manifest: AwdurManifestBuilder | None = None
        """If set, signals that the project has started an update transaction."""

        self.dbpath: pathlib.Path = (
            data_dir or pathlib.Path(".").resolve()
        ) / f"awdur.fossil"
        """The path to the awdur database."""

        self.stats: RepoStats = RepoStats()
        """Statistics about the repository."""

        self.user: User = self._init_db(username or getpass.getuser(), clear_cache)
        """The user account to use."""

    def __getstate__(self) -> object:
        # So that Sphinx can pickle and unpickle this class, we need to mask any fields
        # that are unpickleable.
        state = self.__dict__.copy()

        # Pickling the manifest builder does not make sense, so we should be safe to
        # just ignore it.
        state["manifest"] = None
        return state

    def _init_db(self, username: str, clear_cache: bool) -> User:
        """Initialize the db if needed and return the user's account record."""

        if (existing_db := self.dbpath.exists()) and clear_cache:
            self.logger.debug("Deleting existing database")
            self.dbpath.unlink()
            existing_db = False

        with self.dbcon() as db:
            if existing_db:
                self.logger.debug("Using existing database")
                # TODO: Validate db structure.
            else:
                self.logger.debug("Configuring blank database")
                _ = db.executescript(SCHEMA.read_text())
                self.logger.debug("Applied schema")

                for conf in [
                    Config("aux-schema", "2015-01-24"),
                    Config("content-schema", "2"),
                    Config("hash-policy", "2"),
                    Config("project-code", gen_project_code()),
                    Config("server-code", value=gen_server_code()),
                ]:
                    self.logger.debug("set: %r", conf)
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
            self.logger.debug("user: %r", user.login)

        return user

    @contextmanager
    def dbcon(self):
        """A context manager for connecting to the database."""
        self.logger.debug("Connecting to %r", self.dbpath.as_uri())
        db = sqlite3.connect(self.dbpath)

        yield db

        self.logger.debug("Closing connection to %r", self.dbpath.as_uri())
        db.close()

    def start_update(
        self, comment: str, date: dt.datetime | None = None
    ) -> AwdurManifestBuilder:
        """Start a new project update."""

        if self.manifest is not None:
            self.abort_update()
            raise RuntimeError(
                "Unable to start project update, update already in progress"
            )

        now = date or dt.datetime.now(tz=UTC)

        if (previous_manifest := self.get_awdur_manifest()) is None:
            # Create the root manifest
            self.manifest = pending_manifest = AwdurManifestBuilder.new(
                self.dbpath.as_uri(),
                comment=comment,
                date=now,
                user=self.user,
                logger=self.logger,
            )
            _ = pending_manifest.add_tag("branch", "trunk", propagate=True)
            _ = pending_manifest.add_tag("sym-trunk", propagate=True)
            _ = pending_manifest.add_tag("source", "awdur", propagate=True)

        else:
            self.manifest = pending_manifest = AwdurManifestBuilder.update(
                self.dbpath.as_uri(),
                previous_manifest,
                comment=comment,
                date=now,
                user=self.user,
                logger=self.logger,
            )

        return pending_manifest

    def abort_update(self):
        """Abort the update."""
        if self.manifest is not None:
            self.manifest.abort()
            self.manifest = None

        self.rebuild_metadata()

    def commit_update(self) -> Blob | None:
        """Commit changes to the db.

        This method finalises the manifest, inserts it to the database and commits the
        transaction.

        Returns
        -------
        Blob | None
           The blob containing the committed manifest, if successful
        """

        if (self.manifest) is None:
            raise RuntimeError("Cannot commit update, no update in progress")

        blob = self.manifest.finish()
        self.rebuild_metadata()
        self.manifest = None

        return blob

    def rebuild_metadata(self):
        """Call out to fossil to rebuild the metadata tables."""

        # The majority of the fossil db can be derived from the sequence of artifacts.
        # Rather than attempt to keep up with implementation details of the tool, just
        # run the command provided for this purpose
        result = subprocess.run(
            ["fossil", "rebuild", "--stats", str(self.dbpath)], capture_output=True
        )
        if result.returncode != 0:
            self.logger.error(result.stderr.decode("utf8").strip())
            raise RuntimeError("Unable to rebuild metadata")
        else:
            for line in result.stdout.decode("utf8").splitlines():
                if ":" not in line:
                    continue
                field, value = line.split(":")
                field = field.strip().lower()

                if hasattr(self.stats, field):
                    try:
                        count = int(value.strip())
                    except Exception as exc:
                        count = 0
                        self.logger.error("Unable to parse value: %r", value)

                    setattr(self.stats, field, count)

            self.logger.debug("Rebuilt repository metadata: %r", self.stats)

    def get_awdur_manifest(self, revision: str | None = None) -> Artifact | None:
        """Get the manifest representing awdur's internal state at the given revision.

        Parameters
        ----------
        revision
           Not currently implemented, this function always returns the latest version.

        Returns
        -------
        AwdurManifest | None
           The awdur manifest at the requested revision, or None if not found.
        """
        with self.dbcon() as db:
            cursor = db.execute(
                "SELECT rid FROM awdur_manifests ORDER BY rid DESC LIMIT 1",
            )
            if (row := cursor.fetchone()) is None:
                return None

            rid = row[0]
            if (blob := Artifact.find(db, rid=rid)) is None:
                raise RuntimeError(
                    f"Unable to get awdur manifest, blob rid={rid} not found"
                )

            return blob

    def export(self, project: str, exporter: ProjectExporter, output: pathlib.Path):
        """Export the given project using the given exporter."""

        if self.manifest is not None:
            raise RuntimeError("Cannot export a project while updating.")

        with self.dbcon() as db:
            if (blob := self.get_awdur_manifest()) is None:
                raise RuntimeError("Unable to export project, no projects defined")

        self.render_project(project, blob)
        exporter.export(project, self, output)

    def get_project_names(self) -> list[str]:
        """Return the list of defined project names."""

        with self.dbcon() as db:
            cursor = db.execute(
                "SELECT value FROM awdur_properties WHERE tagname='projects' "
                "ORDER BY rid DESC LIMIT 1",
            )
            if (row := cursor.fetchone()) is not None and (value := row[0]) is not None:
                return value.split(",")
            return []

    def get_project_version(
        self, project: str, revision: str | None = None
    ) -> Artifact | None:
        """Get the manifest representing the given project at the given revision.

        Parameters
        ----------
        project
           The name of the project

        revision
           The project's revision.
           If ``None``, return the latest revision.
        """
        with self.dbcon() as db:
            return _get_project_manifest(db, project, revision)

    def render_project(self, project: str, blob: Artifact | Blob):
        """Render a project's code from the given manifest."""

        if self.manifest is not None:
            raise RuntimeError("Cannot render a project while updating.")

        manifest = Manifest.fromblob(blob)
        timeline = ProjectTimeline.from_manifest(manifest, project)
        self.logger.debug("Timeline: %s", timeline)

        previous_manifest: Artifact | Blob | None = None

        for rev, fileset in timeline:
            self.logger.debug("Exporting revision: %r", rev)
            comment = f"Project export"
            date = dt.datetime.now(tz=UTC)

            if previous_manifest is None:
                # first check-in
                builder = ManifestBuilder.new(
                    self.dbpath.as_uri(),
                    comment=comment,
                    date=date,
                    user=self.user,
                    logger=self.logger,
                )
                builder.add_tag("branch", project, propagate=True)
                builder.add_tag(f"sym-{project}", propagate=True)

            else:
                builder = ManifestBuilder.update(
                    self.dbpath.as_uri(),
                    previous_manifest,
                    comment=comment,
                    date=date,
                    user=self.user,
                    logger=self.logger,
                )

            builder.add_tag("source", blob.uuid)
            builder.add_tag("rev", str(rev))

            env = Environment(
                loader=ProjectTemplateLoader(project, manifest, builder.db)
            )
            # Render each file in this revision
            for filename, file in fileset:
                slots, settings = file.resolve(builder.db)
                context: dict[str, Any] = {
                    "output": {"path": pathlib.Path(filename)},
                    "slots": slots,
                }
                insert_fn = make_code_inserter(context)

                template = env.get_template(settings.get("template", "default"))
                content = template.render(**context, insert=insert_fn)
                _ = builder.add_file(
                    filename,
                    content,
                    permissions=settings.get("permissions"),
                )

            # Check to see if there is an existing manifest at this revision.
            if (pblob := _get_project_manifest(builder.db, project, rev)) is not None:
                existing_manifest = Manifest.fromblob(pblob)

                # Only commit the manifest if the repo checksums are different.
                if existing_manifest.rchecksum != builder.calc_rchecksum():
                    previous_manifest = builder.finish()
                else:
                    # Be sure to discard the in progress manifest to release the db connection.
                    builder.abort()
                    previous_manifest = pblob
            else:
                # Commit the revision
                previous_manifest = builder.finish()

        self.rebuild_metadata()


@dataclasses.dataclass
class FileSpec:
    """Holds the necessary information required to render a file within a project."""

    slots: dict[str, list[tuple[str, str]]] = dataclasses.field(
        default_factory=functools.partial(defaultdict, list)
    )
    """A dictionary mapping content slot names to a list of blob uuids containing the
    actual content."""

    settings: list[str] = dataclasses.field(default_factory=list)
    """A list of blob uuids containing settings to be applied."""

    def resolve(self, db: sqlite3.Connection):
        """Resolve all uuid references and return the actual context."""
        slots: dict[str, list[str]] = {}

        for slotname, uuids in self.slots.items():
            for idx, uuid in uuids:
                if (blob := Artifact.find(db, uuid=uuid)) is None:
                    raise RuntimeError(f"Unable resolve blob {uuid!r}")

                slots.setdefault(slotname, []).append((idx, blob.text))

        settings: dict[str, str] = {}
        # Settings should be sorted in priority order!
        for uuid in self.settings:
            if (blob := Artifact.find(db, uuid=uuid)) is None:
                raise RuntimeError(f"Unable resolve blob {uuid!r}")

            for line in blob.text.splitlines():
                key, value = line.split(":")
                settings[key.strip()] = value.strip()

        return slots, settings


@dataclasses.dataclass
class ProjectFileSet:
    """Represents a tree of files."""

    files: dict[str, FileSpec] = dataclasses.field(
        default_factory=functools.partial(defaultdict, FileSpec)
    )

    def __getitem__(self, key: str):
        return self.files[key]

    def __iter__(self):
        yield from self.files.items()

    def apply_settings(self, filename: str, blob: str):
        """Apply settings to files matching the given filename pattern.

        Parameters
        ----------
        filename
           The file(s) to apply the settings to, can be either an extact filename or
           a glob pattern.

        blob
           The uuid of the blob containing the settings to apply.
        """
        # TODO: Handle specificity
        for fpath, file in self.files.items():
            if fnmatch.fnmatch(fpath, filename):
                file.settings.append(blob)


@dataclasses.dataclass
class ProjectTimeline:
    """Represents the state of a project at each revision."""

    revisions: dict[str, ProjectFileSet] = dataclasses.field(
        default_factory=functools.partial(defaultdict, ProjectFileSet),
    )
    """The set of revisions in the timeline."""

    def __getitem__(self, key: str):
        return self.revisions[key]

    def __iter__(self):
        yield from self.revisions.items()

    @classmethod
    def from_manifest(cls, manifest: Manifest, project_name: str):
        """Given a manifest, construct a project timeline."""

        timeline = cls()

        # First convert the manifest into a set of files at each revision.
        prefix = f"project/{project_name}/file/"
        for path, uuid in (
            (p.removeprefix(prefix), b.blob)
            for p, b in manifest.files.items()
            if p.startswith(prefix)
        ):
            *parts, slot, revision, idx = path.split("/")
            filename = "/".join(parts)
            rev = timeline[revision]

            file = rev[filename]
            file.slots[slot].append((idx, uuid))

        # Now map the settings to each file.
        prefix = f"project/{project_name}/setting/"
        for path, uuid in (
            (p.removeprefix(prefix), b.blob)
            for p, b in manifest.files.items()
            if p.startswith(prefix)
        ):
            # TODO: This isn't quite right, need to handle propogation of settings to
            #       later revisions.
            *parts, revision = path.split("/")
            filename = "/".join(parts)
            rev = timeline[revision]
            rev.apply_settings(filename, uuid)

        return timeline


def make_code_inserter(context):
    """Return the implementation of the 'insert' function to use."""

    def insert(
        lines: list[tuple[str, str]],
        indent: int | str | None = None,
        indentchar: str = " ",
    ) -> str:
        """Insert code into the file."""
        code = "\n\n".join((l for _, l in sorted(lines, key=folgzettel_sort)))

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
{% block footer %}
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

        if (blob := Artifact.find(self.db, uuid=file.blob)) is None:
            raise TemplateNotFound(template)

        self._templates[template] = tmpl = (blob.text, None, None)
        return tmpl


def _get_project_manifest(
    db: sqlite3.Connection, project: str, revision: str | None
) -> Artifact | None:
    """Return the blob containing the given project's manifest at the given revision.

    Parameters
    ----------
    db
       The database connection to use.

    project
       The project name to fetch

    revision
       The revision to retrieve. If not given, the latest revision is returned.

    Returns
    -------
    Artifact | None
       The requested project manifest, if found.
    """
    cursor = db.execute(
        "SELECT rid FROM awdur_project_revisions "
        "WHERE project = ? AND rev LIKE ? "
        "ORDER BY rev, rid DESC LIMIT 1",
        (project, revision or "%"),
    )
    if (row := cursor.fetchone()) is None:
        return None

    rid = row[0]
    if (blob := Artifact.find(db, rid=rid)) is None:
        raise RuntimeError(
            f"Unable to get manifest for project {project!r}, blob rid={rid} not found"
        )

    return blob


def folgzettel_sort(item: str | tuple[str, ...]) -> tuple[int | str, ...]:
    """A key function for use with Python's sorted() function to return a series of
    'folgzettel' numbers in the correct order."""

    if isinstance(item, tuple):
        value = item[0]
    else:
        value = item

    fns = [int, str]
    prefix, *rest = re.split(r"(\d+)", value)
    if prefix != "":
        fns = reversed(fns)
        rest = [prefix, *rest]

    converters = itertools.cycle(fns)
    return tuple(convert(value) for convert, value in zip(converters, rest))


def gen_code_from_uuid():
    # Use uuid4 to get a random data, hash it to get a value compatible with fossil's
    return hashlib.sha1(str(uuid.uuid4()).encode()).hexdigest()


gen_project_code = gen_code_from_uuid
gen_server_code = gen_code_from_uuid
