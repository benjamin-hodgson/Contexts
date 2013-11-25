import random
import string
from unittest import mock
import sure
from contexts.reporting.shared import ReporterComposite


class WhenComposingReporters(object):
    @classmethod
    def examples(cls):
        yield "method", ("abc", 123), {"key": "val"}
        yield "another_method", ("def", 12.3), {"dict": "contents"}
        yield randomword(5), ("xyz",), {"keyword":2+3j}

    def establish_that_the_composite_contains_reporters(self, example):
        self.name, self.args, self.kwargs = example
        self.mock_reporter1, self.mock_reporter2 = mocks = (mock.Mock(), mock.Mock())
        self.composite = ReporterComposite(mocks)

    def because_we_call_a_method_on_the_reporter(self, example):
        getattr(self.composite, self.name)(*self.args, **self.kwargs)

    def it_should_pass_the_arguments_to_the_same_method_in_the_first_mock(self):
        getattr(self.mock_reporter1, self.name).assert_called_once_with(*self.args, **self.kwargs)

    def it_should_pass_the_arguments_to_the_same_method_in_the_second_mock(self):
        getattr(self.mock_reporter2, self.name).assert_called_once_with(*self.args, **self.kwargs)

class WhenQueryingAFailedComposite(object):
    def establish_that_the_composite_contains_a_failed_reporter(self):
        self.composite = ReporterComposite([MockFailedReporter(), MockPassingReporter(), MockDontKnowReporter()])

    def because_we_ask_if_the_run_failed(self):
        self.result = self.composite.failed

    def it_should_say_it_failed(self):
        self.result.should.be.true

class WhenQueryingAPassingComposite(object):
    def establish_that_the_composite_contains_a_failed_reporter(self):
        self.composite = ReporterComposite([MockPassingReporter(), MockPassingReporter(), MockDontKnowReporter()])

    def because_we_ask_if_the_run_failed(self):
        self.result = self.composite.failed

    def it_should_say_it_passed(self):
        self.result.should.be.false


###########################################################
# Test helpers
###########################################################

class MockFailedReporter(object):
    def __init__(self):
        self.failed = True
class MockPassingReporter(object):
    def __init__(self):
        self.failed = False
class MockDontKnowReporter(object):
    pass

def randomword(length):
   return ''.join(random.choice(string.ascii_lowercase) for i in range(length))
