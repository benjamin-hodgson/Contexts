.. _guide:

Guide
=====

.. contents::


Command line usage
------------------
``run-contexts`` will run all test files and folders in the current directory.

``run-contexts {filename}`` will run the tests in the specified file.

``run-contexts {directory}`` will run the tests in the specified directory (or package)
and any subdirectories (or packages).

``run-contexts`` accepts the following command-line flags:

* ``-h`` or ``--help``: Print a help message and exit.
* ``--version``: Print information about which version of Contexts is installed
* ``-s`` or ``--no-capture``: Don't capture stdout during tests. By default, Contexts will prevent stdout from
  being printed to the console unless a test fails. Use this option to disable this.
* ``--teamcity``: Use when the tests are being run in TeamCity. Contexts tries to detect this automatically,
  but the flag is provided in case you have trouble.
* ``-v`` or ``--verbose``: Report tests that pass as well as those that fail.
* ``--no-colour``: Disable output colouring.
* ``--no-random``: Disable test order randomisation. Note that, even with randomisation disabled,
  Contexts makes no promises about the order in which tests will be run.
* ``--no-assert``: Disable 'assertion rewriting' - don't try to add helpful messages to assertions made with
  the `assert` statement.


.. _test-discovery:

Test discovery
--------------
If a *module* contains the words **test** or **spec** in its name, Contexts will
import it and run any tests therein.
If a *folder* has the words 'test' or 'spec' in its name,
Contexts will scan its contents for modules and subfolders matching this pattern.
If a *package* has the words 'test' or 'spec' in its name, Contexts will
import it, and scan the package's contents for modules and subfolders matching this pattern.

If a class has **spec** or **when** in the name, Contexts will treat it as a test case. Test classes
can inherit from ``object`` - there's no need to subclass ``TestCase`` for Contexts to pick up your tests.


Defining tests
--------------
Contexts will instantiate and run each test class once. The methods on the class will be run in
a certain order, depending on their names.

If a method in a test class has an ambiguous name (its name would place it in more than one
of the categories below), Contexts will raise an exception.

By default, Contexts randomises the order in which test classes, and assertions within each class,
will be run. It's therefore important to ensure that all your test cases are independent. Randomisation
can be disabled by supplying the ``--no-random`` flag at the command line. This is not recommended (since you
may inadvertently introduce coupling between your tests), and the order will still be arbitrary and liable
to change between runs.


.. _setup:

``given`` - setting up
~~~~~~~~~~~~~~~~~~~~~~
If the words **establish**, **context**, or **given** appear in a method,
it will be run before the other test methods in the class. 'Establish' methods are typically used
to build test data, instantiate the object under test, set up mock objects,
write test files to the file system, and so on. The purpose of this is to put the system in a known
state before the test begins.

The setup method is run *once for each test class*, to encourage you to ensure your assertions
don't modify any state.
Compare this with the xUnit style, wherein the setup is run before every test method.

There should be *one setup method per class* - Contexts will throw an exception if it finds
more than one method that appears to be a setup method.

Contexts supports inheritance of setup methods.
If a test class has a superclass, the parent's 'establish' method will be run before the child's.
This allows you to share setup code between test classes. The superclass's setup will be run
*even if it has the same name* as the subclass's setup method.


.. _action:

``when`` - acting on the SUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the words 'because', 'when', 'since' or 'after' appear in the name of a method, it is treated
as an 'action' method. Typically, this method will do nothing except call the function under test -
after all, you've set up all your test data in the 'context' method.

The action method is run *once for each test class*, to encourage you to ensure your assertions don't
modify any state.

There should be *one action method per class* - Contexts will throw an exception if it finds
more than one method that appears to be a action method.

The 'because' method will be run immediately after the 'establish' method.

Inheritance of action methods is not supported. The 'because' method will only be run on
the concrete class of the test object.


.. _assertion:

``should`` - assertions
~~~~~~~~~~~~~~~~~~~~~~~
If a method contains the words **it**, **should**, **then**, **must** or **will** in its name, it is treated as an
assertion. Assertion methods should be very granular - one assertion per method,
if possible - and named to describe the *behaviour* you're trying to test (rather than details such as
function names).

Assertions may be made using the ``assert`` statement, or any assertion library which
raises `AssertionError` upon failure.

Each assertion method will be run once, after the 'because' method and before the 'cleanup' method
(see below). Contexts makes no promises about the order in which assertions will be made, and the
order may change between runs, so it's important to ensure that all the assertions on a given class
are independent of one another.

If an assertion fails, all the remaining assertions will still be run, and Contexts will report
precisely which ones failed. Contrast this with the xUnit testing style, wherein a failing assertion
ends the test and any subsequent assertions will not be run.

Contexts supports testing with the ``assert`` statement. No one likes writing their own assertion messages
(especially when you've just labelled the method name descriptively!), so Contexts
tries to supply a useful message if you didn't add one yourself. This is achieved by metaprogramming -
Contexts introspects the source code of your module while it's being imported,
and modifies it to add assertion messages. If this behaviour freaks you out, you can disable it
by supplying a ``--no-assert`` flag at the command line.

You can have as many assertion methods as you like on a single class.


.. _cleanup:

``cleanup``
~~~~~~~~~~~
If the word **cleanup** appears in a method's name, it is treated as a tearing-down method, and run after
all the assertions are finished. The cleanup method is guaranteed to be run, even if exceptions get
raised in the setup, action or assertion methods.

Good tests should leave the world in the state in which they found it.
Cleanup methods are therefore most commonly found in integration tests which modify
the filesystem or database, or otherwise do IO in order to set up the test.

The cleanup method is run *once for each test class*, to encourage you to ensure your assertions
don't modify any state.
Compare this with the xUnit style, wherein the teardown is run after every test method.

There should be *one cleanup method per class* - Contexts will throw an exception if it finds
more than one method that appears to be a cleanup method.

Contexts supports inheritance of cleanup methods.
If a test class has a superclass, the parent's 'cleanup' method will be run after the child's.
This allows you to share cleanup code between test classes. The superclass's cleanup will be run
*even if it has the same name* as the subclass's setup method.

.. _examples:

``examples`` - triangulating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contexts has support for 'examples' - sets of test data for which the whole test is expected to pass.
Examples allow you to triangulate your tests very easily - if you need more test data, simply add a line
to the 'examples' method.

If you define a `classmethod` with the words **examples** or **data** in its name, it is treated as a
test-data-generating method. This method must return an iterable (you can use ``yield``),
and it will be called before testing begins.

For each example returned by the 'examples' method, the test class will be instantiated and run once.
Test methods which accept one argument will have the current example passed into them.
A method which accepts no arguments will be run normally. This allows you to take one of two approaches
to testing using examples. You can accept the example once in the setup and set it as an attribute on `self`,
or you can accept it into every test method.

Other methods
~~~~~~~~~~~~~
Other methods, which do not contain any of the keywords detailed above, are treated as normal
instance methods. They can be called as usual by the other methods of the class.


Catching exceptions
~~~~~~~~~~~~~~~~~~~
Sometimes you need to assert that a given function call will raise a certain type of exception.
You can catch and store an exception -  to make assertions about it later - using Contexts's `catch`
function.

``contexts.catch()`` accepts a function, and runs it inside a ``try`` block.
If an exception gets raised by the function, `catch` returns the exception. If no exception was raised,
it returns ``None``.
Any additional arguments or keyword arguments to ``catch`` are forwarded to the function under test.

You'll typically see ``catch`` in a 'because' method. The caught exception generally gets saved as an
instance attribute, and assertions are made about (for example) its type in assertion methods.


Debugging
~~~~~~~~~
It's often useful to be able to drop into a debugger at a set point in your test run. However, Contexts's
default stdout-capturing behaviour can interfere with this. This can be disabled using ``-s``/``--no-capture``
at the command line. Also provided is a ``set_trace()`` convenience function - add the line
``contexts.set_trace()`` to your code to launch a debugger from that line connected to the *real* stdout.


Timing things
~~~~~~~~~~~~~
Sometimes you need to assert that an action is performant. Contexts provides a ``time()`` convenience function
for this purpose.

``contexts.time()`` measures the execution time of a function and returns the execution time as a float in seconds,
by calling :func:`time.time()` before and after running the function. The precision of ``contexts.time()``
on your platform therefore depends on the precision of :func:`time.time()` on your platform.


Overriding name-based usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sometimes you need to name a test object in such a way that upsets the test runner. Such an example would be
a setup method with the word 'it' in the name.

Contexts provides a built-in plugin which defines a set of decorators for overriding the way an object is named:

* ``@setup`` to mark setup methods
* ``@action`` to mark action methods
* ``@assertion`` to mark assertion methods
* ``@teardown`` to mark cleanup methods
* ``@spec`` or its alias ``@context`` to mark classes as tests

A brief example:

::

    from contexts import setup
    class WhenINameMethodsAmbiguously:
        @setup
        def establish_that_it_has_an_ambiguous_name(self):
            # this method has both 'establish' and 'it' in the name.
            # Contexts will have a hard time discerning its purpose
            # unless we mark it explicitly.


TeamCity
--------
Contexts has support for running tests in `TeamCity <http://www.jetbrains.com/teamcity/>`_.
``run-contexts`` should automatically recognise when a build is being run by TeamCity.
If you have problems, try invoking the test runner with a ``--teamcity`` flag.

Each assertion will be reported to TeamCity as a separate test, and each test file that gets
run will be reported as a separate suite.
Contexts reports failures to TeamCity along with any stack traces, and also captures and
reports any activity on stdout and stderr.

List of keywords
================

=================================== ================================================
Meaning                             Keywords
=================================== ================================================
:ref:`Test folder <test-discovery>` ``test``, ``spec``
:ref:`Test file <test-discovery>`   ``test``, ``spec``
:ref:`Test class <test-discovery>`  ``test``, ``spec``
:ref:`Examples <examples>`          ``example``, ``data``
:ref:`Setup <setup>`                ``establish``, ``context``, ``given``
:ref:`Action <action>`              ``because``, ``since``, ``after``, ``when``
:ref:`Assertion <assertion>`        ``it``, ``should``, ``must``, ``will``, ``then``
:ref:`Cleanup <cleanup>`            ``cleanup``
=================================== ================================================
