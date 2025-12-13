Multiple Blocks
===============

``awdur`` supports combining multiple blocks of code together into a single file.
Say we were writing a program involving triangles, we might first write a function to calculate the perimeter::

  def perimeter(a, b, c):
      return a + b + c

We might then also write a function to calculate the area::

  def area(a, b, c):
      return 0.5 * a * b

Since this is a documentation file, we can make clear the assumptions the above function makes.

.. warning::

   This implementation of ``area`` assumes you have a right-angled triangle, with ``a`` denoting the
   height of the triangle and ``b`` denoting the legnth of the base.

Finally, we may bring this all together into a simple program::

  a, b, c = 3, 4, 5
  P = perimeter(a, b, c)
  A = area(a, b, c)

  print(f"A triangle with sides {a=}, {b=}, {c=} has")
  print(f"- Perimeter, {P=}")
  print(f"- Area, {A=}")
