Contexts
========
[![Build Status](https://travis-ci.org/benjamin-hodgson/Contexts.png?branch=master)](https://travis-ci.org/benjamin-hodgson/Contexts)
[![Documentation Status](https://readthedocs.org/projects/contexts/badge/?version=v0.11.1)](https://readthedocs.org/projects/contexts/?badge=v0.10.2)
[![Requirements Status](https://requires.io/github/benjamin-hodgson/Contexts/requirements.svg?branch=master)](https://requires.io/github/benjamin-hodgson/Contexts/requirements/?branch=master)

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
* Give your tests [**descriptive names**](http://contexts.readthedocs.org/en/latest/guide.html#defining-tests)
  so you can tell what's gone wrong when they fail!
* Run **all the assertions** for each test case, even when one fails!
* Practice 'Example-Driven-Development' with [**parametrised tests**](http://contexts.readthedocs.org/en/latest/guide.html#examples-triangulating)!
* Extend Contexts by writing your own [**plugins**](http://contexts.readthedocs.org/en/latest/plugins.html)!
* Use the `assert` statement and still get [**helpful failure messages**](http://contexts.readthedocs.org/en/latest/guide.html#should-assertions)!
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

Quick start
-----------
Here's an example of a test case that the authors of [Requests](https://github.com/kennethreitz/requests)
might have written, if they were using Contexts.
See the [documentation](http://contexts.readthedocs.org/en/latest)
for [details](http://contexts.readthedocs.org/en/latest/guide.html)
and [more examples](http://contexts.readthedocs.org/en/latest/samples.html).

```python
import requests
# no need to import contexts!

class WhenRequestingAResourceThatDoesNotExist:
    def given_that_we_are_asking_for_a_made_up_resource(self):
        self.uri = "http://www.github.com/itdontexistman"
        self.session = requests.Session()

    def because_we_make_a_request(self):
        self.response = self.session.get(self.uri)

    def the_response_should_have_a_status_code_of_404(self):
        assert self.response.status_code == 404

    def the_response_should_have_an_HTML_content_type(self):
        assert self.response.headers['content-type'] == 'text/html'

    def cleanup_the_session(self):
        self.session.close()
```

### Running your tests
Type `run-contexts` at the command line to discover and run test files and folders in your working directory.

Help
----
All the documentation is stored [on readthedocs](http://contexts.readthedocs.org/en/latest/index.html).
