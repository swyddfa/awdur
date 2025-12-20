Directives
==========

This page documents the custom directives provided by ``awdur``.

.. rst:directive:: code

   ``awdur`` extends the default code block directives, introducing options allowing you to specify where each block of code sits within the project structure.

   .. code-block:: python
      :filename: example.py

      print("Hello, world!")

   In addition to the usual options, ``awdur`` introduces the following options.

   .. rst:option:: filename

      Specify the output file this code block belongs within.
      When the same filename is used across multiple code blocks, their contents will be concatenated in the order that they are encountered.

   .. rst:option:: template

      Specify the template used to render the final file.
      Only needs to be used on one code block within a file.


Sphinx Only
-----------

The following directives are only available when using the Sphinx extension (``awdur.sphinxext``)

.. rst:directive:: code-block
                   sourcecode

   See :rst:dir:`code`.
