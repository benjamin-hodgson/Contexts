Contexts
========
[![Build Status](https://travis-ci.org/benjamin-hodgson/Contexts.png?branch=master)](https://travis-ci.org/benjamin-hodgson/Contexts)

Trello board: https://trello.com/b/uPgp50AF/contexts-development

Contexts is a 'Context-Specification'-style test runner for Python, inspired by C#'s
[`Machine.Specifications`](https://github.com/machine/machine.specifications).

Writing tests which read like sentences can encourage you to focus your testing efforts on the externally
observable behaviour of the code. Contexts is designed around this test-as-sentence idea.
It makes it easier for you to give your tests fluent descriptions by running methods
in sequence based on their names.


Guide
-----
Contexts subscribes to a testing style wherein each class represents a single test case.
The 'arrange-act-assert' pattern is spread out across a whole class, with descriptively-named methods
representing each step in the process.

If certain words appear in the name of an object, Contexts will treat it in a certain way.


### Defining tests
If a _module_ contains the words 'test' or 'spec' in its name, Contexts will
import it and run any tests therein.
If a _folder_ has the words 'test' or 'spec' in its name,
Contexts will scan its contents for modules and subfolders matching this pattern.
If a _package_ has the words 'test' or 'spec' in its name, Contexts will
import it, and scan the package's contents for modules and subfolders matching this pattern.

If a class has 'spec' or 'when' in the name, Contexts will treat it as a test case.
Each test class will be instantiated and run once, following the
'arrange-act-assert' pattern detailed below.

If a methods in a test class has an ambiguous name (its name would place it in more than one
of the categories below), Contexts will raise an exception.

Contexts makes no promises about the order in which test classes, modules, folders or packages
will be run. It's therefore important to ensure that all your test cases are independent.

#### Setting up
If the words 'establish', 'when', or 'given' appear in a method,
it will be run before the other test methods in the class. 'Establish' methods are typically used
to build test data, instantiate the object under test, set up mock objects,
write test files to the file system, and otherwise prepare the test.

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
If a method contains the words 'it', 'should', 'must' or 'will' in its name, it is treated as an
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


Example
-------
Here's an example of a test case that the authors of [Requests](https://github.com/kennethreitz/requests) might have written, if they
were using Contexts.

```python
import requests

# Classes with 'when' in the name are treated as test contexts.
class WhenRequestingAResourceThatDoesNotExist(object):
    # No need to subclass TestCase for Contexts to run your test.
    def establish_that_we_are_asking_for_a_made_up_resource(self):
        # methods with 'establish' in the name are run first,
        # and are used to put the system in a known state before the test begins.
        self.uri = "http://www.github.com/itdontexistman"
        self.session = requests.Session()

    def because_we_make_a_request(self):
        # 'because' methods represent the action you take, and are run after the 'establish'.
        # This will typically be a call to the method under test.
        self.response = self.session.get(self.uri)

    def the_response_should_have_a_status_code_of_404(self):
        # methods with 'should' in the name are used for making
        # assertions about the new state of your system.
        assert self.response.status_code == 404

    def the_response_should_have_an_HTML_content_type(self):
        assert self.response.headers['content-type'] == 'text/html'

    def it_should_raise_an_HTTPError_when_we_ask_it_to(self):
        # 'catch' runs a function that you expect to raise an exception, and returns the exception.
        # In the real world this assertion would be another class, but I wanted to show you 'catch'!
        exception = contexts.catch(self.response.raise_for_status)
        assert isinstance(exception, requests.exceptions.HTTPError)

    def cleanup_the_session(self):
        # 'cleanup' methods are run last, even if an error occurred during the test.
        self.session.close()

if __name__ == '__main__':
    import contexts
    contexts.main()
```
