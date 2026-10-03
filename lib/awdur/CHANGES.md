## v0.2.0 - 2026-10-03

### Breaking Changes

- Metadata options on codeblocks have been renamed:

  - `:filename:` -> `:in-file:`
  - `:project:` -> `:in-project:`
  - `:slot:` -> `:in-slot:`

  File templates are no longer set using a codeblock, instead use the `:use-template:` option on the new `awdur:file(s)::` directive.

  The `awdur:project-tree::` directive has been renamed to `awdur:project::`.

  The html project export has been temporarily removed.

  The concept of a "default filename" has been removed, all files must now be explicitly named.

  ([#44](https://github.com/swyddfa/awdur/issues/44))

### Features

- Awdur now renders its internal state to a [fossil](https://fossil-scm.org/) compatible database meaning you should be able to use `fossil ui` or `fossil open` on it to inspect the contents.
  This means the `fossil` cli program is now a runtime requirement for `awdur`.

  There is now `awdur:file::` and `awdur:files::` directives for providing file-level metadata. 

  Awdur now has the concept of "revisions" where you can describe the evolution of file contents by providing revision numbers using the `:at-revision:` option with codeblocks. ([#44](https://github.com/swyddfa/awdur/issues/44))

### Fixes

- ``awdur`` should no longer fail to handle docinfo / field list items that do not provide a value. ([#39](https://github.com/swyddfa/awdur/issues/39))


## v0.1.0 - 2026-09-03

### Features

- It's now possible to name code blocks by passing them a `:slot:` option to override the default `content` slot.
  Slots can be included in other code blocks using the `{{ insert(slots.name) }}` template function. ([#18](https://github.com/swyddfa/awdur/issues/18))

### Enhancements

- `.. code-blocks::` managed by awdur now include a header that indicates which file the content belongs to ([#22](https://github.com/swyddfa/awdur/issues/22))
- It's now possible to set default values for options like `:filename:` by using reStructuredText's field list syntax.
  Currently, they take effect from the point they are entered into the document onwards, though it might make sense to scope it to the current document section... ([#31](https://github.com/swyddfa/awdur/issues/31))

### Fixes

- When using `awdur export`, `.. include::` directives should now resolve correctly.

  The `awdur export` command should no longer crash when processing documents containing `.. contents::` directives. ([#17](https://github.com/swyddfa/awdur/issues/17))


## v0.0.1 - 2024-01-20


### Misc

- Initial release ([#14](https://github.com/swyddfa/awdur/issues/14))
