Multiple Files
==============

As projects grow beyond a certain complexity, you are going to want to produce more than one code file.
To support this ``awdur`` allows you to specify the destination filename as part of the code block definition.

Fibbonacci
----------

Below is a function to calculate the n\ :sup:`th` Fibonacci number

.. code:: python
   :filename: fib.py

   def fib(n):
       if n == 0 or n == 1:
           return n
       return fib(n-1) + fib(n - 2)

Which we can then use to print the first 10 Fibonacci numbers

.. code:: python
   :filename: fib.py

   nums = [str(fib(n)) for n in range(1, 11)]
   print(f"The first 10 Fibonacci numbers are: {', '.join(nums)}")


Square Numbers
--------------

Here is a function for calculating the square of a number

.. code:: python
   :filename: square.py

   def square(n):
       return n * n

Which we can then use to print the first 10 square numbers

.. code:: python
   :filename: square.py

   nums = [str(square(n)) for n in range(1,11)]
   print(f"The first 10 square numbers are: {', '.join(nums)}")
