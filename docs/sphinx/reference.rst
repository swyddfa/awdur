.. _sphinx-reference:

Reference
=========

Directives
----------

In addition to the :ref:`core directives <usage-directives>` provided by the tool, the following directives are available when using the Sphinx extension

.. rst:directive:: code-block
                   sourcecode

   See :rst:dir:`code`.


.. rst:directive:: awdur:render

   .. note::

      This directive only has an effect with html outputs.

   Run the given ``<filename>`` through the ``awdur render`` cli command and embed the result into the page using an ``iframe``
