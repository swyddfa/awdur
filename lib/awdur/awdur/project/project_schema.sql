-- Schema for awdur's internal representation of a project.
--
-- Currently just a subset of the main Fossil database schema
--
-- see: https://fossil-scm.org/home/file?&name=src%252Fschema.c

CREATE TABLE IF NOT EXISTS blob(
  rid INTEGER PRIMARY KEY,
  rcvid INTEGER,
  size INTEGER,
  uuid TEXT UNIQUE NOT NULL,
  content BLOB,
  CHECK( length(uuid)>=40 AND rid>0 )
);


CREATE TABLE IF NOT EXISTS delta(
  rid INTEGER PRIMARY KEY,
  srcid INTEGER NOT NULL REFERENCES blob
);
CREATE INDEX IF NOT EXISTS delta_i1 ON delta(srcid);


-- Create a table, loosely inspired by fossil's 'event' table to keep
-- track of commits.
CREATE TABLE IF NOT EXISTS event(
  type TEXT,
  mtime DATETIME,
  objid INTEGER PRIMARY KEY,
  uid TEXT,
  comment TEXT
);
CREATE INDEX IF NOT EXISTS event_i1 ON event(mtime);


CREATE VIEW IF NOT EXISTS artifact(
  rid,
  rcvid,
  size,
  atype,
  srcid,
  hash,
  content
) AS SELECT blob.rid,rcvid,size,1,srcid,uuid,content
FROM blob LEFT JOIN delta ON (blob.rid=delta.rid)
