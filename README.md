Contexts
========
[![Build Status](https://travis-ci.org/benjamin-hodgson/Contexts.png?branch=master)](https://travis-ci.org/benjamin-hodgson/Contexts)

Trello board: https://trello.com/b/uPgp50AF/contexts-development

Contexts is a 'Context-Specification'-style test runner for Python, inspired by C#'s
[`Machine.Specifications`](https://github.com/machine/machine.specifications).

Writing tests which read like sentences can encourage you to focus your testing efforts on the externally
observable behaviour of the code. Contexts can make this easy for you, by running test methods in sequence based on their names.


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
        # In the real world, this assertion would be another class, but I wanted to show you 'catch'!
        exception = contexts.catch(self.response.raise_for_status)
        assert isinstance(exception, requests.exceptions.HTTPError)

    def cleanup_the_session(self):
        # 'cleanup' methods are run last, even if an error occurred during the test.
        self.session.close()

if __name__ == '__main__':
    import contexts
    contexts.main()
```

