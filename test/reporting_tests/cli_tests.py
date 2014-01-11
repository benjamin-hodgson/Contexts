import datetime
from io import StringIO
from unittest import mock
from contexts import reporting
from . import tools


class WhenPrintingASuccessSummary:
    def in_the_context_of_a_successful_run(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.SummarisingReporter(self.stringio)

        ctx1 = tools.create_context()
        ctx2 = tools.create_context()
        assertion1 = tools.create_assertion()
        assertion2 = tools.create_assertion()
        assertion3 = tools.create_assertion()

        self.reporter.context_started(ctx1.name, ctx1.example)
        self.reporter.assertion_started(assertion1)
        self.reporter.assertion_passed(assertion1)
        self.reporter.assertion_started(assertion2)
        self.reporter.assertion_passed(assertion2)
        self.reporter.context_ended(ctx1.name, ctx1.example)

        self.reporter.context_started(ctx2.name, ctx2.example)
        self.reporter.assertion_started(assertion3)
        self.reporter.assertion_passed(assertion3)
        self.reporter.context_ended(ctx2.name, ctx2.example)

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended(tools.create_test_run())

    def it_should_print_the_summary_to_the_stream(self):
        assert self.stringio.getvalue() == (
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")

    def it_should_say_it_passed(self):
        assert not self.reporter.failed


class WhenPrintingAFailureSummary:
    def establish_that_a_test_has_failed(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.SummarisingReporter(self.stringio)

        context = tools.create_context("made.up_context")
        assertion = tools.create_assertion("made.up.assertion_1")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        exception = tools.build_fake_assertion_error(tb1, "Gotcha")

        self.reporter.context_started(context.name, context.example)
        self.reporter.assertion_started(assertion)
        self.reporter.assertion_failed(assertion, exception)
        self.reporter.context_ended(context.name, context.example)

    def because_the_test_run_ends(self):
        self.reporter.test_run_ended(tools.create_test_run())

    def it_should_print_the_failure_tracebacks(self):
        assert self.stringio.getvalue() == ("""
----------------------------------------------------------------------
made up context
  FAIL: made up assertion 1
    Traceback (most recent call last):
      File "made_up_file.py", line 3, in made_up_function
        frame1
      File "another_made_up_file.py", line 2, in another_made_up_function
        frame2
    reporting_tests.tools.FakeAssertionError: Gotcha
----------------------------------------------------------------------
FAILED!
1 context, 1 assertion: 1 failed, 0 errors
""")

    def it_should_say_it_failed(self):
        assert self.reporter.failed

class WhenTimingATestRun:
    def context(self):
        self.fake_now = datetime.datetime(2013, 10, 22, 13, 41, 0)
        self.fake_soon = datetime.timedelta(seconds=10, milliseconds=490)

        class FakeDateTime(datetime.datetime):
            now = mock.Mock(return_value=self.fake_now)
        self.FakeDateTime = FakeDateTime

        self.test_run = tools.create_test_run()
        self.stringio = StringIO()
        self.reporter = reporting.cli.TimedReporter(self.stringio)

    def because_we_run_a_test_run(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            self.reporter.test_run_started(self.test_run)
            datetime.datetime.now.return_value += self.fake_soon
            self.reporter.test_run_ended(self.test_run)

    def it_should_report_the_total_time_for_the_test_run(self):
        assert self.stringio.getvalue() == "(10.5 seconds)\n"
