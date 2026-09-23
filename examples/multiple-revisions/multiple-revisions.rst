Multiple Revisions
==================

No software is perfect and chances are the code you write will need to evolve over time.
However, it can still be useful to refer to older versions of the code as it will often be simpler and still capture the main ideas present in the newer, more complicated code.
Seeing the code evolve, with an extended discussion of the thoughts behind it can be a great way to see where the motivations come from.

For this reason, awdur allows you to construct a narrative for your project through revisions.

Consider the following code.

.. code:: python
   :filename: fizzbuzz.py

   for i in range(1, 26):
       print(i)

By default this is going to be assigned the revision ``1``

Fizz
----

But now we implement the fizz part of the algorithm, we can say that we are at revision ``2``

.. code:: python
   :filename: fizzbuzz.py
   :revision: 2

   for i in range(1, 26):
       if i % 3 == 0:
           print("fizz")
       else:
           print(i)

Fizz Buzz
---------

Then the full fizz buzz algorithm will be given below in revision ``3``

.. code:: python
   :filename: fizzbuzz.py
   :revision: 3

   for i in range(1, 26):
       if i % 3 == 0 and i % 5 == 0:
           print('fizzbuzz')
       elif i % 3 == 0:
           print('fizz')
       elif i % 5 == 0:
           print('buzz')
       else:
           print(i)

Buzz
----

Revisions do not need to be numbers.

There may come a time when you decide to order changes, or that it's worth introducing an intermediate revision.
awdur supports alphanumeric revisions like you might see in a "folgezettel" allowing revisions to be inserted between any two revisions, without renumbering.

.. code:: python
   :filename: fizzbuzz.py
   :revision: 2a

   for i in range(1, 26):
       if i % 3 == 0:
           print('fizz')
       elif i % 5 == 0:
           print('buzz')
       else:
           print(i)

