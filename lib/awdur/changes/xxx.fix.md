`awdur` can now handle chains of delta compressed blobs.

When multiple revisions for a project exist, `awdur` should now export the latest one by default.

When exporting files with multiple revisions, `awdur` now applies changes from a revision on top of the previous one. 
This is most noticable in a file composed of multiple slots, where content only needs to be provided for slots that have changed.
