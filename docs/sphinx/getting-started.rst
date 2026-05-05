Getting Started
===============

Awdur can also be used as a `Sphinx <https://www.sphinx-doc.org/en/master/>`__ extension to set it up, you first need to ensure that ``awdur`` package is installed alongisde Sphinx in your environment

.. code-block:: console

   $ pip install awdur

It also needs to be added to your list of extensions in your project's ``conf.py``

.. code-block:: python

   extensions = [
       ...
       "awdur.sphinxext",
   ]
