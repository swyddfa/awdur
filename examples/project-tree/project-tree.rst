Project Tree
============

Using the ``awdur:project-tree`` directive, you can insert an interactive view allowing you to browse the files included in a project.

.. awdur:project-tree::

For details on the code itself, see below

Hello World
-----------

The code below is a valid "Hello, World!" application in Python.

.. code:: python
   :filename: hello.py

   print("Hello, World!")


Triangles
---------

Say we were writing a program involving triangles, we might first write a function to calculate the perimeter

.. code:: python
   :filename: shapes/triangle.py

   def perimeter(a, b, c):
       return a + b + c

We might then also write a function to calculate the area

.. code:: python
   :filename: shapes/triangle.py

   def area(a, b, c):
       return 0.5 * a * b

Since this is a documentation file, we can make clear the assumptions the above function makes.

.. warning::

   This implementation of ``area`` assumes you have a right-angled triangle, with ``a`` denoting the
   height of the triangle and ``b`` denoting the legnth of the base.

Finally, we may bring this all together into a simple program

.. code:: python
   :filename: shapes/triangle.py

   a, b, c = 3, 4, 5
   P = perimeter(a, b, c)
   A = area(a, b, c)

   print(f"A triangle with sides {a=}, {b=}, {c=} has")
   print(f"- Perimeter, {P=}")
   print(f"- Area, {A=}")

Fibbonacci
----------

Below is a function to calculate the n\ :sup:`th` Fibonacci number

.. code:: python
   :filename: math/fib.py

   def fib(n):
       if n == 0 or n == 1:
           return n
       return fib(n-1) + fib(n - 2)

Which we can then use to print the first 10 Fibonacci numbers

.. code:: python
   :filename: math/fib.py

   nums = [str(fib(n)) for n in range(1, 11)]
   print(f"The first 10 Fibonacci numbers are: {', '.join(nums)}")


Square Numbers
--------------

Here is a function for calculating the square of a number

.. code:: python
   :filename: math/square.py

   def square(n):
       return n * n

Which we can then use to print the first 10 square numbers

.. code:: python
   :filename: math/square.py

   nums = [str(square(n)) for n in range(1,11)]
   print(f"The first 10 square numbers are: {', '.join(nums)}")
