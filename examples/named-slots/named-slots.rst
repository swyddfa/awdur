:project: example

.. awdur:project-tree::

The Reader
----------

:filename: reader.py

Going by the notes in the `guide <https://github.com/kanaka/mal/blob/master/process/guide.md#step-1-read-and-print>`__ we should create a ``Reader`` object.

.. code:: python

   class Reader:
       def __init__(self):
           self.tokens = []
           self.pos = 0

   {{ insert(slots['reader-methods'], indent=4) }}

It is responsible for managing a stream of tokens and should provide the following methods

- A ``next`` method to return the current token and advances the position.

  .. code:: python
     :slot: reader-methods

     def next(self):
         tok = self.tokens[self.pos]
         self.pos += 1
         return tok

- A ``peek`` method that simply returns the current token

  .. code:: python
     :slot: reader-methods

     def peek(self):
         return self.tokens[self.pos]

In the main file

.. code:: python
   :filename: main.py

   from reader import Reader

The Evaluator
-------------

:filename: evaluator.py

.. code:: python

   class Evaluator: ...
