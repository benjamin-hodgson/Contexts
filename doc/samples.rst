Code samples
============

A simple test case
------------------
Here's an example of a test case that the authors of `Requests <https://github.com/kennethreitz/requests>`_
might have written, if they were using Contexts. See the :ref:`Guide <guide>` for details.

::

    import requests
    import contexts

    class WhenRequestingAResourceThatDoesNotExist:
        def establish_that_we_are_asking_for_a_made_up_resource(self):
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

    if __name__ == '__main__':
        contexts.main()


Triangulation
-------------
Here's a brief example of Contexts's triangulation feature. We're asserting that the
various different types of numbers in Python can all be multiplied by 0 to produce the expected result.

::

    class WhenMultiplyingANumberByZero:
        @classmethod
        def examples_of_numbers(cls):
            yield 0
            yield -6
            yield 3
            yield 1.6
            yield 6 + 2j

        def because_we_multiply_by_0(self, example):
            self.result = example * 0

        def it_should_return_0(self):
            assert self.result == 0


If you yield tuples from the `examples` method, and you accept multiple arguments to the test methods,
Contexts will unpack the tuple and pass it in as separate arguments.

::

    class WhenMultiplyingTwoNumbers:
        @classmethod
        def examples_of_numbers_and_their_products(cls):
            yield 1, 12, 12
            yield -3.2, 2, -6.4
            yield 6 + 2j, 9, 54 + 18j

        def because_we_multiply_the_two(self, x, y, expected):
            self.result = x * y

        def it_should_equal_what_we_expected(self, x, y, expected):
            assert self.result == expected


If you accept only one argument to a test method, but you yield tuples, Contexts will not unpack the tuple.

::

    class WhenIYieldTuples:
        @classmethod
        def examples(cls):
            yield 'abc', 123
            yield [], {}

        def it_should_give_me_tuples(self, example):
            assert isinstance(example, tuple)
