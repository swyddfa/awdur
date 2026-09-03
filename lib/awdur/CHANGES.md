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
