Template Basics
===============

By default, ``awdur`` will simply concatenate code blocks together.

However, it's sometimes useful to perform some additional processing on the code blocks before saving them to a file.
For example, when writing Emacs Lisp your files should always have a header comment and a final call to the ``provide`` function, as shown below.

.. code:: emacs-lisp

   ;;; <filename>.el --- Description

   <code goes here>

   (provide '<filename>)

This structure can be expressed in a template removing the need to include random code blocks into your documents, just so you can generate the final file correctly.

Defining Templates
------------------

A template can be defined using the ``.. awdur:template::`` directive.
``awdur`` uses `Jinja <https://jinja.palletsprojects.com/en/stable/>`__ for its template engine.

.. awdur:template:: elisp-module

   {% extends "default" %}

   {% block header %};;; {{ path.name }} --- Description

   {% endblock %}

   {% block footer %}

   (provide '{{ path.stem }}){% endblock %}


Using Templates
---------------

To use a template, reference its name from at least one of the code blocks within the file.

For example, the code block below defines a function to compute the area of a triangle.

.. code:: emacs-lisp
   :filename: triangle.el
   :template: elisp-module

   (defun triangle-area (a b c)
     (* 0.5 a b))

And this defines a function to compute the perimeter, note that now we've the template once we don't need to repeat it.

.. code:: emacs-lisp
   :filename: triangle.el

   (defun triangle-perimeter (a b c)
     (+ a b c))

Of course, the whole point of defining a template is being able to reuse it across multiple files.

.. code:: emacs-lisp
   :filename: rectangle.el
   :template: elisp-module

   (defun rectangle-area (w h)
     (* w h))

   (defun rectangle-perimeter (w h)
     (* 2 (+ w h))
