Contexts
========
[![Build Status](https://travis-ci.org/benjamin-hodgson/Contexts.png?branch=master)](https://travis-ci.org/benjamin-hodgson/Contexts)

Dead simple descriptive testing for Python. No custom decorators, no context managers,
no `.feature` files, no fuss.

Trello board: https://trello.com/b/uPgp50AF/contexts-development

Cheese Shop: https://pypi.python.org/pypi/Contexts

Contexts is a 'Context-Specification'-style test framework for Python, inspired by C#'s
[`Machine.Specifications`](https://github.com/machine/machine.specifications).

Writing tests which read like sentences can encourage you to focus your testing efforts on the externally
observable behaviour of the code. Contexts is designed around this test-as-sentence idea.
It makes it easier for you to give your tests fluent descriptions, because it runs methods
in sequence based on their names.

Installation
------------
The easy way:
```
pip install contexts
```

The geeky way:
```
git clone https://github.com/benjamin-hodgson/Contexts.git
cd Contexts
python setup.py install
```

Example
-------
Here's an example of a test case that the authors of [Requests](https://github.com/kennethreitz/requests)
might have written, if they were using Contexts. See the [Guide](#guide) below for details.

```python
import requests
import contexts

class WhenRequestingAResourceThatDoesNotExist(object):
    def establish_that_we_are_asking_for_a_made_up_resource(self):
        self.uri = "http://www.github.com/itdontexistman"
        self.session = requests.Session()

    def because_we_make_a_request(self):
        self.response = self.session.get(self.uri)

    def the_response_should_have_a_status_code_of_404(self):
        assert self.response.status_code == 404

    def the_response_should_have_an_HTML_content_type(self):
        assert self.response.headers['content-type'] == 'text/html'

    def it_should_raise_an_HTTPError_when_we_ask_it_to(self):
        # In the real world, this assertion would be a whole test class of its own.
        # I put it in because I wanted to demonstrate 'catch()'!
        exception = contexts.catch(self.response.raise_for_status)
        assert isinstance(exception, requests.exceptions.HTTPError)

    def cleanup_the_session(self):
        self.session.close()

if __name__ == '__main__':
    contexts.main()
```

Guide
-----
Contexts subscribes to a testing style wherein each class represents a single test case.
The 'arrange-act-assert' pattern is spread out across a whole class, with descriptively-named methods
representing each step in the process.

If certain words appear in the name of an object, Contexts will treat it in a certain way.

### Command line usage
`run-contexts` will run all test files and folders in the current directory.

`run-contexts {filename}` will run the tests in the specified file.

`run-contexts {directory}` will run the tests in the specified directory (or package)
and any subdirectories (or packages).

`run-contexts` accepts the following flags:
  * `-s` or `--no-capture`: Don't capture stdout during tests. By default, Contexts will prevent stdout from
    being printed to the console unless a test fails. Use this option to disable this.
  * `--teamcity`: Use when the tests are being run in TeamCity. Contexts tries to detect this automatically,
    but the flag is provided in case you have trouble.

### Test discovery
If a _module_ contains the words 'test' or 'spec' in its name, Contexts will
import it and run any tests therein.
If a _folder_ has the words 'test' or 'spec' in its name,
Contexts will scan its contents for modules and subfolders matching this pattern.
If a _package_ has the words 'test' or 'spec' in its name, Contexts will
import it, and scan the package's contents for modules and subfolders matching this pattern.

If a class has 'spec' or 'when' in the name, Contexts will treat it as a test case. Test classes
can inherit from `object` - there's no need to subclass `TestCase` for Contexts to pick up your tests.

### Defining test classes
Contexts will instantiate and run each test class once, following the
'arrange-act-assert' pattern detailed below.

If a method in a test class has an ambiguous name (its name would place it in more than one
of the categories below), Contexts will raise an exception.

Contexts makes no promises about the order in which test classes, modules, folders or packages
will be run. It's therefore important to ensure that all your test cases are independent.

#### Setting up
If the words 'establish', 'when', or 'given' appear in a method,
it will be run before the other test methods in the class. 'Establish' methods are typically used
to build test data, instantiate the object under test, set up mock objects,
write test files to the file system, and so on. The purpose of this is to put the system in a known
state before the test begins.

The setup method is run _once for each test class_, to encourage you to ensure your assertions
don't modify any state.
Compare this with the xUnit style, wherein the setup is run before every test method.

There should be _one setup method per class_ - Contexts will throw an exception if it finds
more than one method that appears to be a setup method.

Contexts supports inheritance of setup methods.
If a test class has a superclass, the parent's 'establish' method will be run before the child's.
This allows you to share setup code between test classes. The superclass's setup will be run
_even if it has the same name_ as the subclass's setup method.

#### Acting on the system under test
If the words 'because', 'when', 'since' or 'after' appear in the name of a method, it is treated
as an 'action' method. Typically, this method will do nothing except call the function under test -
after all, you've set up all your test data in the 'context' method.

The action method is run _once for each test class_, to encourage you to ensure your assertions don't
modify any state.

There should be _one action method per class_ - Contexts will throw an exception if it finds
more than one method that appears to be a action method.

The 'because' method will be run immediately after the 'establish' method.

Inheritance of action methods is not supported. The 'because' method will only be run on
the concrete class of the test object.

#### Making assertions about your action
If a method contains the words 'it', 'should', 'then', 'must' or 'will' in its name, it is treated as an
assertion. Good style suggests that assertion methods should be very granular - one assertion per method,
if possible - and named to describe the _behaviour_ you're trying to test (rather than details such as
function names).

Assertions may be made using the `assert` statement, or any assertion library which
raises `AssertionError` upon failure. Contexts makes a great partner with
[Sure](https://github.com/gabrielfalcao/sure)'s fluent assertions.

Each assertion method will be run once, after the 'because' method and before the 'cleanup' method
(see below). Contexts makes no promises about the order in which assertions will be made, and the
order may change between runs, so it's important to ensure that all the assertions on a given class
are independent of one another (they do not modify any state).

If an assertion fails, all the remaining assertions will still be run, and Contexts will report
precisely which ones failed. Contrast this with the xUnit testing style, wherein a failing assertion
ends the test and any subsequent assertions will not be run.

You can have as many assertion methods as you like on a single class.

#### Cleaning up
If the word 'cleanup' appears in a method's name, it is treated as a tearing-down method, and run after
all the assertions are finished. The cleanup method is guaranteed to be run, even if exceptions get
raised in the setup, action or assertion methods.

Good tests should leave the world in the state in which they found it.
Cleanup methods are therefore most commonly found in integration tests which modify
the filesystem or database, or otherwise do IO in order to set up the test.

The cleanup method is run _once for each test class_, to encourage you to ensure your assertions
don't modify any state.
Compare this with the xUnit style, wherein the teardown is run after every test method.

There should be _one cleanup method per class_ - Contexts will throw an exception if it finds
more than one method that appears to be a cleanup method.

Contexts supports inheritance of cleanup methods.
If a test class has a superclass, the parent's 'cleanup' method will be run after the child's.
This allows you to share cleanup code between test classes. The superclass's cleanup will be run
_even if it has the same name_ as the subclass's setup method.

#### Triangulating
Contexts has support for 'examples' - sets of test data for which the whole test is expected to pass.
Examples allow you to triangulate your tests very easily - if you need more test data, simply add a line
to the 'examples' method.

If you define a `classmethod` with the words 'examples' or 'data' in its name, it is treated as a
test-data-generating method. This method must return an iterable (you can use a generator if you like),
and it will be called before testing begins.

For each example returned by the 'examples' method, the test class will be instantiated and run once.
Test methods which accept one argument will have the current example passed into them.
A method which accepts no arguments will be run normally. This allows you to take one of two approaches
to testing using examples. You can accept the example once in the setup and set it as an attribute on `self`,
or you can accept it into every test method.

Here's a brief example. We're asserting that the various different types of numbers in Python
can all be multiplied by 0 to produce the expected result.

```python
class SpecWithExamples(object):
    @classmethod
    def examples(cls):
        yield 0
        yield -6
        yield 3
        yield 1.6
        yield 6 + 2j
    def because_we_multiply_by_0(self, example):
        self.result = example * 0
    def it_should_return_0(self):
        assert self.result == 0
```

#### Catching exceptions
Sometimes you need to assert that a given function call will raise a certain type of exception.
You can catch and store an exception -  to make assertions about it later - using Contexts's `catch`
function.

`contexts.catch()` accepts a function with no parameters and runs the function in a 'try' block.
If an exception gets raised by the function, `catch` returns the exception. If no exception was raised,
it returns `None`.

You'll typically see `catch` in a 'because' method. The caught exception generally gets saved as an
instance attribute, and assertions are made about (for example) its type in assertion methods.

#### Other methods
Other methods, which do not contain any of the keywords detailed above, are treated as normal
instance methods. They can be called as usual by the other methods of the class.
