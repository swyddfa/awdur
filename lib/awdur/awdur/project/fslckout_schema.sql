-- fslckout database schema
--
-- Provides the schema for the *.fslckout db representing a checkout
-- from a main *.fossil repo.
--
-- see: https://fossil-scm.org/home/file?&name=src%252Fschema.c
CREATE TABLE vfile(
  id INTEGER PRIMARY KEY,
  vid INTEGER REFERENCES blob,
  chnged INT DEFAULT 0,
  deleted BOOLEAN DEFAULT 0,
  isexe BOOLEAN,
  islink BOOLEAN,
  rid INTEGER,
  mrid INTEGER,
  mtime INTEGER,
  pathname TEXT,
  origname TEXT,
  mhash TEXT,
  UNIQUE(pathname,vid)
);


CREATE TABLE vmerge(
  id INTEGER REFERENCES vfile,
  merge INTEGER,
  mhash TEXT
);
CREATE UNIQUE INDEX vmergex1 ON vmerge(id,mhash);


CREATE TABLE vvar(
  name TEXT PRIMARY KEY NOT NULL,
  value CLOB,
  CHECK( typeof(name)='text' AND length(name)>=1 )
) WITHOUT ROWID;
