import datetime
from io import StringIO
from unittest import mock
from contexts.plugins.reporting import cli
from .. import tools


class WhenPrintingFinalCountsForAnEmptyRun:
    def context(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)
    def because_a_test_run_ends(self):
        self.reporter.test_run_ended()
    def it_should_output_zeroes(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
PASSED!
0 contexts, 0 assertions
""")


class WhenPrintingFinalCountsForASuccessfulRun:
    def in_the_context_of_a_successful_run(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)

        ctx1 = type('', (), {})
        ctx2 = type('', (), {})

        self.reporter.context_started(ctx1,'')
        self.reporter.assertion_started(lambda: None)
        self.reporter.assertion_passed(lambda: None)
        self.reporter.assertion_started(lambda: None)
        self.reporter.assertion_passed(lambda: None)
        self.reporter.context_ended(ctx1,'')

        self.reporter.context_started(ctx2,'')
        self.reporter.assertion_started(lambda: None)
        self.reporter.assertion_passed(lambda: None)
        self.reporter.context_ended(ctx2,'')

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended()

    def it_should_output_the_correct_numbers(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")


class WhenPrintingFinalCountsAfterAnAssertionFails:
    def establish_that_an_assertion_has_failed(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)

        self.reporter.assertion_failed(lambda: None, Exception())

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended()

    def it_should_count_one_failure(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
FAILED!
0 contexts, 0 assertions: 1 failed, 0 errors
""")


class WhenPrintingFinalCountsAfterAnAssertionErrors:
    def establish_that_a_test_has_failed(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)

        self.reporter.assertion_errored(lambda: None, Exception())

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended()

    def it_should_count_one_error(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
FAILED!
0 contexts, 0 assertions: 0 failed, 1 error
""")


class WhenPrintingFinalCountsAfterAContextErrors:
    def establish_that_a_test_has_failed(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)

        self.reporter.context_errored("", '', Exception())

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended()

    def it_should_count_one_error(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
FAILED!
0 contexts, 0 assertions: 0 failed, 1 error
""")


class WhenPrintingFinalCountsAfterATestClassErrors:
    def establish_that_a_test_has_failed(self):
        self.stringio = StringIO()
        self.reporter = cli.FinalCountsReporter(self.stringio)

        self.reporter.test_class_errored("", Exception())

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended()

    def it_should_count_one_error(self):
        assert self.stringio.getvalue() == (
"""\
----------------------------------------------------------------------
FAILED!
0 contexts, 0 assertions: 0 failed, 1 error
""")


class WhenTimingATestRun:
    def context(self):
        self.fake_now = datetime.datetime(2013, 10, 22, 13, 41, 0)
        self.fake_soon = datetime.timedelta(seconds=10, milliseconds=490)

        class FakeDateTime(datetime.datetime):
            now = mock.Mock(return_value=self.fake_now)
        self.FakeDateTime = FakeDateTime

        self.stringio = StringIO()
        self.reporter = cli.TimedReporter(self.stringio)

    def because_we_run_a_test_run(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            self.reporter.test_run_started()
            datetime.datetime.now.return_value += self.fake_soon
            self.reporter.test_run_ended()

    def it_should_report_the_total_time_for_the_test_run(self):
        assert self.stringio.getvalue() == "(10.5 seconds)\n"
