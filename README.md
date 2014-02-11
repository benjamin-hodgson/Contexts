Contexts
========
[![Trello board](http://codehum.com/static/media/project/trello-icon2.png)](https://trello.com/b/uPgp50AF/contexts-development)
[![Build Status](https://travis-ci.org/benjamin-hodgson/Contexts.png?branch=master)](https://travis-ci.org/benjamin-hodgson/Contexts)

Dead simple descriptive testing for Python. No custom decorators, no context managers,
no `.feature` files, no fuss.

-----------------------------

Contexts is a 'Context-Specification'-style test framework for Python 3.3 and above, inspired by C#'s
[`Machine.Specifications`](https://github.com/machine/machine.specifications).
It aims to be flexible and extensible, and is appropriate for unit, integration and acceptance testing. Read more at the [Huddle Dev Blog](http://tldr.huddle.com/blog/Write-Your-Tests-In-Another-Language/).

Test written with Contexts resemble the grammar of ['Given/When/Then'](http://martinfowler.com/bliki/GivenWhenThen.html)-style
specifications. Writing tests which read like user-centric sentences can encourage you to
focus on the behaviour, not the implementation, of your code.
Contexts takes cues from [Behaviour Driven Development](http://dannorth.net/introducing-bdd/),
but it aims to be useful for more than just acceptance testing (unlike Cucumber or FitNesse).

Cool features
-------------
* Give your tests [**descriptive names**](https://github.com/benjamin-hodgson/Contexts/wiki/Guide#wiki-defining-tests)
  so you can tell what's gone wrong when they fail!
* Run **all the assertions** for each test case, even when one fails!
* Practice 'Example-Driven-Development' with [**parametrised tests**](https://github.com/benjamin-hodgson/Contexts/wiki/Guide#wiki-triangulating)!
* Extend Contexts by writing your own [**plugins**](https://github.com/benjamin-hodgson/Contexts/wiki/Plugins)!
* Use the `assert` statement and still get [**helpful failure messages**](https://github.com/benjamin-hodgson/Contexts/wiki/Guide#wiki-making-assertions-about-your-action)!
* **Test all the things**!

Installation
------------
Contexts is on [the Cheese Shop](https://pypi.python.org/pypi/Contexts), so you can install it the easy way:
```
pip install contexts
```

If you want the bleeding-edge version, you can install it the geeky way:
```
git clone https://github.com/benjamin-hodgson/Contexts.git
cd Contexts
python setup.py install
```

Contexts has no compulsory external dependencies. There is an optional dependency -
if you like red and green colours in the output from your test runner
(and who doesn't!), you need to install [Colorama](https://pypi.python.org/pypi/colorama).

Example
-------
Here's an example of a test case that the authors of [Requests](https://github.com/kennethreitz/requests)
might have written, if they were using Contexts.
See the [wiki](https://github.com/benjamin-hodgson/Contexts/wiki)
for [details](https://github.com/benjamin-hodgson/Contexts/wiki/Guide)
and [more examples](https://github.com/benjamin-hodgson/Contexts/wiki/Examples).

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
```

Running your tests
------------------
Type `run-contexts` at the command line to discover and run test files and folders in your working directory.

Help
----
All the documentation is stored in the [wiki](https://github.com/benjamin-hodgson/Contexts/wiki).
