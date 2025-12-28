Multiple Projects
=================

Awdur allows for multiple code projects to be embedded within a single documentation artifact.
Where relevant awdur's directives accept a ``:project:`` option that allow you to specify which project it should be assoicated with.

The ``awdur:project-tree`` directive accepts a project name as an argument.

Hello World
-----------

Where no project name is given, the name ``default`` will be used as... well, the default.

.. awdur:project-tree::

The code below is a valid "Hello, World!" application in Python.

.. code:: python
   :filename: hello.py

   print("Hello, World!")


Shapes
------

This project deals with geometric shapes

.. awdur:project-tree:: shapes

Setup
^^^^^

The following template is used when defining an elisp module in this project.

.. awdur:template:: elisp-module
   :project: shapes

   {% extends "default" %}

   {% block header %};;; {{ path.name }} --- Description

   {% endblock %}

   {% block footer %}

   (provide '{{ path.stem }}){% endblock %}

Triangles
^^^^^^^^^

The code block below defines a function to compute the area of a triangle.

.. code:: emacs-lisp
   :project: shapes
   :filename: triangle.el
   :template: elisp-module

   (defun triangle-area (a b c)
     (* 0.5 a b))

And this defines a function to compute the perimeter, note that now we've the template once we don't need to repeat it.

.. code:: emacs-lisp
   :project: shapes
   :filename: triangle.el

   (defun triangle-perimeter (a b c)
     (+ a b c))

Rectangles
^^^^^^^^^^

The following code deals with rectangles.

.. code:: emacs-lisp
   :project: shapes
   :filename: rectangle.el
   :template: elisp-module

   (defun rectangle-area (w h)
     (* w h))

   (defun rectangle-perimeter (w h)
     (* 2 (+ w h))

Math
----

This project deals with number sequences

.. awdur:project-tree:: math

Fibbonacci
^^^^^^^^^^

Below is a function to calculate the n\ :sup:`th` Fibonacci number

.. code:: python
   :project: math
   :filename: fib.py

   def fib(n):
       if n == 0 or n == 1:
           return n
       return fib(n-1) + fib(n - 2)

Which we can then use to print the first 10 Fibonacci numbers

.. code:: python
   :project: math
   :filename: fib.py

   nums = [str(fib(n)) for n in range(1, 11)]
   print(f"The first 10 Fibonacci numbers are: {', '.join(nums)}")


Square Numbers
^^^^^^^^^^^^^^

Here is a function for calculating the square of a number

.. code:: python
   :project: math
   :filename: square.py

   def square(n):
       return n * n

Which we can then use to print the first 10 square numbers

.. code:: python
   :project: math
   :filename: square.py

   nums = [str(square(n)) for n in range(1,11)]
   print(f"The first 10 square numbers are: {', '.join(nums)}")
