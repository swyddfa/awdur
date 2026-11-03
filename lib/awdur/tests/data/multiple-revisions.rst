Hello World
===========

This is the simplest use of awdur, a reStructuredText file with containing a code block linked to a filename.
The code below is a valid "Hello, World!" application in Python.

.. code:: python
   :in-file: hello.py
   :at-revision: 1

   print("Hello, World!")


With a few tweaks we can make the file executable.
First add a shebang.

.. code:: python
   :in-file: hello.py
   :at-revision: 2

   #!/usr/bin/env python
   print("Hello, World!")

Then delcare the file to be executable.

.. awdur:file:: hello.py
   :permissions: x
