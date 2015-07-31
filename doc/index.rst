.. Contexts documentation master file, created by
   sphinx-quickstart on Wed Sep 17 21:51:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Contexts
========
Dead simple descriptive testing for Python. No custom decorators, no context managers, no .feature files, no fuss.

About
-----
Contexts is a 'Context-Specification'-style test framework for Python 3.3 and above, inspired by C#'s
`Machine.Specifications <https://github.com/machine/machine.specifications/>`_.
It aims to be flexible and extensible, and is appropriate for unit, integration and acceptance testing. Read more at the `Huddle Dev Blog <http://tldr.huddle.com/blog/Write-Your-Tests-In-Another-Language/>`_.

Test written with Contexts resemble the grammar of `Given, When, Then <http://martinfowler.com/bliki/GivenWhenThen.html>`_-style
specifications. Writing tests which read like user-centric sentences can encourage you to
focus on the behaviour, not the implementation, of your code.
Contexts takes cues from `Behaviour Driven Development <http://dannorth.net/introducing-bdd/>`_,
but it aims to be useful for more than just acceptance testing.

Quick start
-----------

Install Contexts and optionally `colorama <https://pypi.python.org/pypi/colorama>`_.

.. code-block:: bash

    $ pip install contexts colorama

Create a file in the current directory called ``test.py``. Put a class in that file; this will be your test. The class's name must include the word ``When``.

Spread the *arrange, act, assert* steps of your test across three separate methods in the class; their names must match the :ref:`supported keywords <keywords>`.

::

    class WhenAddingTwoNumbers:
        def given_the_two_numbers(self):
            self.x = 4
            self.y = 2
        def when_i_add_them(self):
            self.result = self.x + self.y
        def it_should_produce_the_correct_sum(self):
            assert self.result == 6


Run the test!

.. code-block:: bash

    $ run-contexts
    .
    ----------------------------------------------------------------------
    PASSED!
    1 context, 1 assertion
    (0.1 seconds)


Table of contents
-----------------
.. toctree::
   :maxdepth: 2

   guide
   plugins
   samples

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
