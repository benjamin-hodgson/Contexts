from unittest import mock
import contexts


class WhenCatchingAnException:
    def given_a_function_that_throws_an_exception(self):
        self.thrown = ValueError("test exception")

        def throwing_function(a, b, c, d=[]):
            self.call_args = (a,b,c,d)
            raise self.thrown
        self.throwing_function = throwing_function

    def because_we_call_catch(self):
        self.caught = contexts.catch(self.throwing_function, 3, c='yes', b=None)

    def it_should_call_the_function_with_the_supplied_arguments(self):
        assert self.call_args == (3, None, 'yes', [])

    def it_should_catch_and_return_the_exception(self):
        assert self.caught is self.thrown


class WhenTimingSomething:
    def context(self):
        self.mock_clock = mock.Mock(return_value = 10)
        self.time_diff = 100.7
        def slow_function(a,b,c,d=[]):
            self.call_args = (a,b,c,d)
            self.mock_clock.return_value += self.time_diff
        self.slow_function = slow_function

    def because_we_run_a_slow_function(self):
        with mock.patch("time.time", self.mock_clock):
            self.result = contexts.time(self.slow_function, 3, c='yes', b=None)

    def it_should_call_the_function_with_the_supplied_arguments(self):
        assert self.call_args == (3, None, 'yes', [])

    def it_should_return_the_time_difference_in_seconds(self):
        assert self.result == self.time_diff
