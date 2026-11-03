from __future__ import annotations

import datetime as dt
import hashlib
import logging
import operator
import pathlib
import sqlite3
import typing

from .db import ASCII
from .db import Artifact
from .db import Blob
from .db import Manifest
from .db import Rcvfrom
from .db import Tag
from .db import User

if typing.TYPE_CHECKING:
    from .db import FilePermissions
    from .db import FileStatus
    from .db import TagType


class ManifestBuilder:
    """A helper class for constructing fossil manifests."""

    def __init__(
        self,
        manifest: Manifest,
        rcvfrom: Rcvfrom,
        db: sqlite3.Connection,
        logger: logging.Logger | None = None,
    ):
        self.manifest: Manifest = manifest
        """The manifest instance to populate"""

        self.rcvfrom: Rcvfrom = rcvfrom
        """The rcvfrom instance representing the current 'transaction'"""

        self.db: sqlite3.Connection = db
        """The database connection."""

        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        """The logger instance to use."""

    @classmethod
    def new(
        cls,
        dbpath: str,
        *,
        comment: str,
        date: dt.datetime,
        user: User,
        logger: logging.Logger | None = None,
    ):
        """Create a new root manifest."""

        if user.uid is None:
            raise ValueError("User must have an uid")

        manifest = Manifest(comment=comment, date=date, user=user.login)

        db = sqlite3.connect(dbpath, uri=True)
        rcvfrom = Rcvfrom.create(user.uid, mtime=date).insert(db)
        builder = cls(manifest, rcvfrom, db, logger)

        builder.logger.debug("Creating root manifest")
        builder.logger.debug("dbpath=%r", dbpath)
        builder.logger.debug("rcvid=%s", rcvfrom.rcvid)

        return builder

    @classmethod
    def update(
        cls,
        dbpath: str,
        previous: Artifact | Blob,
        *,
        comment: str,
        date: dt.datetime,
        user: User,
        logger: logging.Logger | None = None,
    ):
        """Create an update based on the given manifest."""

        if user.uid is None:
            raise ValueError("User must have an uid")

        if previous.uuid is None:
            raise ValueError("Previous manifest blob must have a uuid")

        predecessor = Manifest.fromblob(previous)
        manifest = Manifest(
            comment=comment,
            date=date,
            files=predecessor.files.copy(),  # manifests should specify every file
            previous=previous.uuid,
            user=user.login,
        )

        db = sqlite3.connect(dbpath, uri=True)
        rcvfrom = Rcvfrom.create(user.uid, mtime=date).insert(db)
        builder = cls(manifest, rcvfrom, db, logger)

        builder.logger.debug("Creating update to %r", predecessor)
        builder.logger.debug("dbpath=%r", dbpath)
        builder.logger.debug("rcvid=%s", rcvfrom.rcvid)

        return builder

    def get_artifact(self, uuid: str) -> Artifact | None:
        """Return the artifact with the given uuid, if defined."""
        return Artifact.find(self.db, uuid=uuid)

    def add_file(
        self,
        filename: str,
        content: str,
        permissions: FilePermissions = "w",
        old_filename: pathlib.Path | None = None,
    ) -> tuple[Manifest.File, FileStatus]:
        """Add a file to the manifest.

        If necessary, the file's content will be automatically inserted into the
        database as a blob.

        Parameters
        ----------
        filename
           The file's path relative to the root of the repo.

        content
           The file's content

        permissions
           The file's permissions

        old_filename
           If the file was renamed, the previous name for the file.

        Returns
        -------
        Manifest.File, FileStatus
           The file's manifest record and a string indicating if the file is new, has
           changed relative to the previous version or unchanged
        """
        fpath = pathlib.Path(filename)
        blob = Blob.create(content, self.rcvfrom.rcvid)

        # Check to see if this blob is already present in the db.
        #
        # *Note:* This is not the same as 'no change to the previous version', we could
        # be reverting a file to a previous state, or duplicating content that was
        # stored elsewhere in the tree.
        if (existing_blob := Blob.find(self.db, uuid=blob.uuid)) is None:
            blob = blob.insert(self.db)
        else:
            blob = existing_blob

        file, status = self.manifest.add_file(
            fpath, blob.uuid, permissions, old_filename
        )
        self.logger.debug(
            "+ %s, file %s (%s blob)",
            file,
            status,
            "new" if existing_blob is None else "existing",
        )
        return file, status

    def add_tag(self, name: str, value: str | None = None, propagate: bool = False):
        """Add a tag to the manifest.

        Parameters
        ----------
        name
           The name of the tag.

        value
           The value of the tag (making it a property).

        propagate
           If ``True``, indicate that the tag should be propagated to all descendents of
           the manifest under construction.

        Returns
        -------
        Tag
           The constructed tag
        """
        tag_type: TagType = "*" if propagate else "+"
        tag = Tag(tag_type, name, "*", value=value)
        self.manifest.add_tag(tag)
        return tag

    def abort(self):
        """Rollback and abort the update."""
        self.logger.debug("Aborting update")
        self.db.rollback()

        self.logger.debug("Closing connection to %r", self.db)
        self.db.close()

    def commit(self):
        """Commit changes and close the db connection."""
        self.logger.debug("Committing update")
        self.db.commit()

        self.logger.debug("Closing connection to %r", self.db)
        self.db.close()

    def finish(self) -> Blob | None:
        """Finish building the manifest and return the completed blob, if an update was
        made."""

        if self.manifest.comment == "":
            raise ValueError("Invalid manifest: a check-in comment is required")

        if self.manifest.date is None:
            raise ValueError("Invalid manifest: a check-in date is required")

        if self.manifest.user == "":
            raise ValueError(
                "Invalid manifest: a check-in must be associated with a user"
            )

        for t in self.manifest.tags:
            if t.uuid != "*":
                raise ValueError(
                    "Invalid tag: manifest tags must target '*' (i.e. self)"
                )

        self.manifest.rchecksum = self.calc_rchecksum()

        # Check that a meaningful change has been applied
        if (previous := self.manifest.previous) is not None:
            if (pblob := Artifact.find(self.db, uuid=previous)) is None:
                raise RuntimeError(
                    "Unable to validate update, predecessor manifest "
                    f"uuid={previous!r} not found"
                )

            predecessor = Manifest.fromblob(pblob)
            if self.manifest.rchecksum == predecessor.rchecksum:
                self.logger.debug("Skipping update, no meaningful changes")
                self.abort()
                return None

        # Looks good, let's commit!
        manifest = self.manifest.build()
        mblob = Blob.create(manifest, self.rcvfrom.rcvid).insert(self.db)
        self.logger.debug("Manifest: %r\n%s", mblob, manifest)
        self.commit()
        return mblob

    def calc_rchecksum(self):
        """Calculate the repository checksum for the current state of the manifest."""
        rchecksum = hashlib.md5()
        for _, file in sorted(self.manifest.files.items(), key=operator.itemgetter(0)):
            if (file_blob := Artifact.find(self.db, uuid=file.blob)) is None:
                raise RuntimeError(
                    "Unable to finish manifest, content for blob "
                    f"uuid={file.blob!r} not found "
                )

            text = file_blob.text
            item = (
                f"{file.filename}{chr(ASCII.SPACE)}"
                f"{len(text)}{chr(ASCII.NEWLINE)}"
                f"{text}"
            )
            rchecksum.update(item.encode())

        return rchecksum.hexdigest()


class AwdurManifestBuilder(ManifestBuilder):
    """A helper class for constructing fossil manifests that represent the state of an
    awdur repository."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stale_sources: set[str] = set(
            f.filename for f in self.manifest.find_files(prefix="src/")
        )
        """Records the set of source filename that should be considered stale and
        removed."""

        self.stale_fragments: set[str] = set()
        """Records the set of framgents that have been marked as stale and can be
        overwritten/discarded."""

    def finish(self):
        """Finish building the manifest and return the completed blob."""

        # Any sources still considered stale should be removed.
        for stale_src in self.stale_sources:
            self._mark_fragments_as_stale(stale_src)
            stale_path = pathlib.Path(stale_src)
            self.logger.debug("- %s (stale)", self.manifest.get_file(stale_path))
            self.manifest.delete_file(stale_path)

        # Along with any stale fragments.
        for filename in self.stale_fragments:
            self.manifest.delete_file(pathlib.Path(filename))

        # Record the projects defined.
        projects = sorted(
            {p.split("/")[1] for p in self.manifest.files if p.startswith("project/")}
        )
        _ = self.add_tag("projects", ",".join(projects))
        return super().finish()

    def add_src(self, src: str, filename: str) -> tuple[Manifest.File, FileStatus]:
        """Add a source (e.g. an rst file) to the manifest

        If the given ``filename`` already exsits, any code fragments associated with it
        will be marked as stale and will (eventually) be removed unless explicitly
        re-added to the manifest.

        Parameters
        ----------
        src
           The source text to be added.

        filename
           The filename that contained the source.

        Returns
        -------
        tuple[Manifest.File, FileStatus]
           The manifest record associated with this source and a string indicating if
           the file is new, has changed relative to the previous version or unchanged.
        """
        fpath = f"src/{filename}"
        file, status = self.add_file(fpath, src)

        if status == "updated":
            self._mark_fragments_as_stale(fpath)

        # Be sure to remove the file from the set of stale sources
        self.stale_sources -= set([file.filename])
        return file, status

    def _mark_fragments_as_stale(self, src: str):
        """Mark any fragments associated with the given src as stale."""
        srctag = src.replace("/", "-")
        for fragment in self.manifest.find_files(contains=srctag):
            self.stale_fragments.add(fragment.filename)
            self.logger.debug("- %s (stale)", fragment)

    def add_fragment(
        self,
        code: str,
        srcpath: str,
        destpath: str,
        project: str,
        revision: str = "1",
        slot: str = "content",
    ) -> tuple[Manifest.File, FileStatus]:
        """Add a code fragment to a project.

        Parameters
        ----------
        code
           The code fragment itself.

        srcpath
           The path of the source that contributed the fragment.

        destpath
           The filename within the project to associate the fragment with.

        project
           The destination project's name.

        revision
           The revision to associate the fragment with.

        slot
           The slot to associate the fragment with.

        Returns
        -------
        tuple[Manifest.File, FileStatus]
           The fragment's manifest record and a string indicating if it is new, updated
           or unchanged.
        """
        # Add a fragment to map the code to its destination in the project.
        #
        # To try and minimise the amount of random re-ordering of fragments within a
        # slot we'll include the srcpath in the fragment path...
        frag_prefix = "/".join(
            [
                "project",
                project,
                "file",
                destpath,
                slot,
                revision,
                srcpath.replace("/", "-") + ":",
            ]
        )
        return self._add_fragment(frag_prefix, code)

    def _add_fragment(
        self, frag_prefix: str, code: str
    ) -> tuple[Manifest.File, FileStatus]:
        """Add the given fragment, reusing slots where possible."""

        fragments = list(self.manifest.find_files(prefix=frag_prefix))
        stale_fragments = [f for f in fragments if f.filename in self.stale_fragments]

        # ... and then use the next entry that is still considered free.
        if len(stale_fragments) > 0:
            fragment = stale_fragments[0]
            fragment, status = self.add_file(fragment.filename, code)
        else:
            frag_id = len(fragments) + 1
            frag_path = f"{frag_prefix}{frag_id}"
            fragment, status = self.add_file(frag_path, code)

        # Make sure if this was considered a stale blob we undo that.
        self.stale_fragments -= set([fragment.filename])
        return fragment, status

    def set_file_properties(
        self,
        filename: str,
        project: str,
        permissions: FilePermissions | None = None,
        template: str | None = None,
        revision: str = "1",
    ) -> tuple[Manifest.File, FileStatus]:
        """Set additional properties for the given filename.

        Parameters
        ----------
        filename
           An exact filename, or a filename glob pattern to apply the properties to

        project
           The project name

        permissions
           If set, set the file's permissions

        template
           If set, use the given template name

        revision
           The revision at which the settings apply.
        """
        lines: list[str] = []
        if template is not None:
            lines.append(f"template: {template}")

        if permissions is not None:
            lines.append(f"permissions: {permissions}")

        content = "\n".join(lines)

        fpath = f"project/{project}/setting/{filename}/{revision}"
        return self.add_file(fpath, content)

    def add_template(
        self, name: str, content: str, project: str
    ) -> tuple[Manifest.File, FileStatus]:
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
        return self.add_file(fpath, content)
