Simple
======

Simple examples of ``awdur`` usage


Single file, single block
-------------------------

The following code block defines the entire contents of the file ``hello.py``

.. code-block::
   :filename: hello.py

   print("Hello, World!")


Single file, multiple blocks
----------------------------

The following sequence of blocks combine to form the file ``sequence.py``

.. code-block::
   :filename: sequence.py

   print("One")

.. code-block::
   :filename: sequence.py

   print("Two")

.. code-block::
   :filename: sequence.py

   print("Three")

Single file, multiple source files
----------------------------------

The file ``multi_source.py`` is composed of three blocks, the of which is below

.. code-block::
   :filename: multi_source.py

   print("One")

The second can be found in :doc:`multi/file2` and the third in :doc:`multi/file3`.
Notice that the order in which the files are processed by Sphinx dictates the order in which the code blocks are inserted into the output file.

.. toctree::
   :caption: Multi-File

   multi/file2
   multi/file3
