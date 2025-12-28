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

   .. rst:option:: project

      Specify the name of the project to associate the code block with.
      If not given the default name ``default`` will be used.

.. rst:directive:: awdur:template

   Define a custom template to use with a project.
   See :doc:`/examples/inline-templates` for example usage.

   .. rst:option:: project

      Specify the name of the project to associate the template with.
      If not given the default name ``default`` will be used.

.. rst:directive:: awdur:project-tree

   .. note::

      This directive only has an effect with html outputs.

   Insert an interactive file explorer for code files produced by the given project.
   If no name is given, the default name ``default`` will be used.

   See :doc:`/examples/project-tree` and :doc:`/examples/multiple-projects` for example usage.


Sphinx Only
-----------

The following directives are only available when using the Sphinx extension (``awdur.sphinxext``)

.. rst:directive:: code-block
                   sourcecode

   See :rst:dir:`code`.


.. rst:directive:: awdur:render

   .. note::

      This directive only has an effect with html outputs.

   Run the given ``<filename>`` through the ``awdur render`` cli command and embed the result into the page using an ``iframe``
