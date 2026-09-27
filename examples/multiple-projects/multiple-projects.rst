Multiple Projects
=================

Awdur allows for multiple code projects to be embedded within a single documentation artifact.
Where relevant awdur's directives accept an ``:in-project:`` option that allow you to specify which project it should be assoicated with.

The ``awdur:project-tree`` directive accepts a project name as an argument.

Hello World
-----------

Where no project name is given, the name ``default`` will be used as... well, the default.

.. awdur:project::

The code below is a valid "Hello, World!" application in Python.

.. code:: python
   :in-file: hello.py

   print("Hello, World!")


Shapes
------

This project deals with geometric shapes

.. awdur:project:: shapes

   .. awdur:files:: *.el
      :use-template: elisp-module


.. The below sets default metadata for this document section.

:in-project: shapes

Setup
^^^^^

The following template is used when defining an elisp module in this project.

.. awdur:template:: elisp-module

   {% extends "default" %}

   {% block header %};;; {{ output.path.name }} --- Description

   {% endblock %}

   {% block footer %}
   (provide '{{ output.path.stem }})
   {% endblock %}


Triangles
^^^^^^^^^

:in-file: triangle.el

The code block below defines a function to compute the area of a triangle.

.. code:: emacs-lisp

   (defun triangle-area (a b c)
     (* 0.5 a b))

And this defines a function to compute the perimeter, note that now we've the template once we don't need to repeat it.

.. code:: emacs-lisp

   (defun triangle-perimeter (a b c)
     (+ a b c))

Rectangles
^^^^^^^^^^

The following code deals with rectangles.

.. code:: emacs-lisp
   :in-file: rectangle.el

   (defun rectangle-area (w h)
     (* w h))

   (defun rectangle-perimeter (w h)
     (* 2 (+ w h))

Math
----

This project deals with number sequences

.. awdur:project:: math

:in-project: math

Fibbonacci
^^^^^^^^^^

:in-file: fib.py

Below is a function to calculate the n\ :sup:`th` Fibonacci number

.. code:: python

   def fib(n):
       if n == 0 or n == 1:
           return n
       return fib(n-1) + fib(n - 2)

Which we can then use to print the first 10 Fibonacci numbers

.. code:: python

   nums = [str(fib(n)) for n in range(1, 11)]
   print(f"The first 10 Fibonacci numbers are: {', '.join(nums)}")


Square Numbers
^^^^^^^^^^^^^^

:in-file: square.py

Here is a function for calculating the square of a number

.. code:: python

   def square(n):
       return n * n

Which we can then use to print the first 10 square numbers

.. code:: python

   nums = [str(square(n)) for n in range(1,11)]
   print(f"The first 10 square numbers are: {', '.join(nums)}")
