import datetime
import sys
from io import StringIO
from unittest import mock
import sure
import contexts
from contexts import reporting
from . import test_doubles


class WhenWatchingForDots(object):
    def context(self):
        self.stringio = StringIO()
        self.result = reporting.TextResult(self.stringio)
        self.fake_context = contexts.core.Context([],[],[],[],"context")
        self.fake_assertion = contexts.core.Assertion(None, "assertion")

    def because_we_run_some_assertions(self):
        self.result.context_started(self.fake_context)

        self.result.assertion_started(self.fake_assertion)
        self.result.assertion_passed(self.fake_assertion)
        self.first = self.stringio.getvalue()

        self.result.assertion_started(self.fake_assertion)
        self.result.assertion_passed(self.fake_assertion)
        self.second = self.stringio.getvalue()

        self.result.assertion_started(self.fake_assertion)
        self.result.assertion_failed(self.fake_assertion, test_doubles.FakeException())
        self.third = self.stringio.getvalue()

        self.result.assertion_started(self.fake_assertion)
        self.result.assertion_errored(self.fake_assertion, test_doubles.FakeException())
        self.fourth = self.stringio.getvalue()

        self.result.context_errored(self.fake_context, test_doubles.FakeException())
        self.fifth = self.stringio.getvalue()

    def it_should_print_a_dot_for_the_first_pass(self):
        self.first.should.equal('.')

    def it_should_print_a_dot_for_the_second_pass(self):
        self.second.should.equal('..')

    def it_should_print_an_F_for_the_failure(self):
        self.third.should.equal('..F')

    def it_should_print_an_E_for_the_assertion_error(self):
        self.fourth.should.equal('..FE')

    def it_should_print_an_E_for_the_ctx_error(self):
        self.fifth.should.equal('..FEE')

class WhenPrintingASuccessfulResult(object):
    def in_the_context_of_a_successful_run(self):
        # We don't want it to try and print anything while we set it up
        self.stringio = StringIO()
        self.result = reporting.TextResult(StringIO())

    def because_we_run_some_tests(self):
        self.result.suite_started(None)

        self.result.context_started(None)
        self.result.assertion_started(None)
        self.result.assertion_passed(None)
        self.result.assertion_started(None)
        self.result.assertion_passed(None)
        self.result.context_ended(None)

        self.result.context_started(None)
        self.result.assertion_started(None)
        self.result.assertion_passed(None)
        self.result.context_ended(None)

        self.result.stream = self.stringio
        self.result.suite_ended(None)

    def it_should_print_the_summary_to_the_stream(self):
        self.stringio.getvalue().should.equal(
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")

class WhenPrintingAFailureResult(object):
    def in_the_context_of_a_failed_run(self):
        self.result = reporting.TextResult(StringIO())
        self.stringio = StringIO()

        self.assertion1 = contexts.core.Assertion(None, "made.up.assertion_1")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
                    ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception1 = test_doubles.build_fake_exception(tb1, "Gotcha")

        self.assertion2 = contexts.core.Assertion(None, "made.up.assertion_2")
        tb2 = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
                    ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        self.exception2 = test_doubles.build_fake_exception(tb2, "you fail")

        self.context3 = contexts.core.Context([],[],[],[],"made.up_context")
        tb3 = [('made_up_file_5.py', 1, 'made_up_function_5', 'frame5'),
                    ('made_up_file_6.py', 2, 'made_up_function_6', 'frame6')]
        self.exception3 = test_doubles.build_fake_exception(tb3, "oh dear")

    def because_we_run_some_tests(self):
        self.result.suite_started(None)

        self.result.context_started(None)
        self.result.assertion_started(self.assertion1)
        self.result.assertion_errored(self.assertion1, self.exception1)
        self.result.assertion_started(self.assertion2)
        self.result.assertion_failed(self.assertion2, self.exception2)
        self.result.context_ended(None)

        self.result.context_started(self.context3)
        self.result.context_errored(self.context3, self.exception3)

        self.result.stream = self.stringio
        self.result.suite_ended(None)

    def it_should_print_a_traceback_for_each_failure(self):
        self.stringio.getvalue().should.equal("""
======================================================================
ERROR: made.up.assertion_1
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file.py", line 3, in made_up_function
    frame1
  File "another_made_up_file.py", line 2, in another_made_up_function
    frame2
test.test_doubles.FakeException: Gotcha
======================================================================
FAIL: made.up.assertion_2
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file_3.py", line 1, in made_up_function_3
    frame3
  File "made_up_file_4.py", line 2, in made_up_function_4
    frame4
test.test_doubles.FakeException: you fail
======================================================================
ERROR: made.up_context
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file_5.py", line 1, in made_up_function_5
    frame5
  File "made_up_file_6.py", line 2, in made_up_function_6
    frame6
test.test_doubles.FakeException: oh dear
----------------------------------------------------------------------
FAILED!
2 contexts, 2 assertions: 1 failed, 2 errors
""")


class WhenTimingATestRun(object):
    def context(self):
        self.fake_now = datetime.datetime(2013, 10, 22, 13, 41, 0)
        self.fake_soon = datetime.timedelta(seconds=10, milliseconds=490)

        class FakeDateTime(datetime.datetime):
            now = mock.Mock(return_value=self.fake_now)
        self.FakeDateTime = FakeDateTime

        self.stringio = StringIO()
        self.result = reporting.TimedTextResult(self.stringio)

    def because_we_run_a_suite(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            self.result.suite_started(None)
            datetime.datetime.now.return_value += self.fake_soon
            self.result.suite_ended(None)

    def it_should_report_the_total_time_for_the_test_run(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
PASSED!
0 contexts, 0 assertions
(10.5 seconds)
""")

class WhenCapturingStdOut(object):
    def context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

        self.fake_context = contexts.core.Context([],[],[],[],"context")
        self.fake_assertion = contexts.core.Assertion(None, "assertion")

        self.stringio = StringIO()
        # we don't want the output to be cluttered up with dots
        self.result = reporting.CapturingTextResult(StringIO())

    def because_we_print_some_stuff(self):
        # It'd be nice if this could be done using the context managers
        self.result.suite_started(None)

        self.result.context_started(self.fake_context)
        print("passing context")
        self.result.assertion_started(self.fake_assertion)
        print("passing assertion")
        print("to stderr", file=sys.stderr)
        self.result.assertion_passed(self.fake_assertion)
        self.result.context_ended(self.fake_context)

        self.result.context_started(self.fake_context)
        print("failing context")
        self.result.assertion_started(self.fake_assertion)
        print("failing assertion")
        self.result.assertion_failed(self.fake_assertion, test_doubles.FakeException())
        self.result.assertion_started(self.fake_assertion)
        print("erroring assertion")
        self.result.assertion_errored(self.fake_assertion, test_doubles.FakeException())
        self.result.context_ended(self.fake_context)

        self.result.context_started(self.fake_context)
        print("erroring context")
        self.result.assertion_started(self.fake_assertion)
        print("assertion in erroring context")
        self.result.assertion_passed(self.fake_assertion)
        self.result.context_errored(self.fake_context, test_doubles.FakeException())

        self.result.context_started(self.fake_context)
        self.result.assertion_started(self.fake_assertion)
        # don't print anything
        self.result.assertion_failed(self.fake_assertion, test_doubles.FakeException())
        self.result.context_ended(self.fake_context)

        self.result.stream = self.stringio
        self.result.suite_ended(None)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_let_stderr_through(self):
        self.fake_stderr.getvalue().should.equal("to stderr\n")

    def it_should_output_the_captured_stdout_for_the_failures(self):
        self.stringio.getvalue().should.equal("""
======================================================================
FAIL: assertion
----------------------------------------------------------------------
test.test_doubles.FakeException
-------------------- >> begin captured stdout << ---------------------
failing context
failing assertion
--------------------- >> end captured stdout << ----------------------
======================================================================
ERROR: assertion
----------------------------------------------------------------------
test.test_doubles.FakeException
-------------------- >> begin captured stdout << ---------------------
failing context
failing assertion
erroring assertion
--------------------- >> end captured stdout << ----------------------
======================================================================
ERROR: context
----------------------------------------------------------------------
test.test_doubles.FakeException
-------------------- >> begin captured stdout << ---------------------
erroring context
assertion in erroring context
--------------------- >> end captured stdout << ----------------------
======================================================================
FAIL: assertion
----------------------------------------------------------------------
test.test_doubles.FakeException
----------------------------------------------------------------------
FAILED!
4 contexts, 5 assertions: 2 failed, 2 errors
""")

    def cleanup_stdout_and_stderr(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr


if __name__ == "__main__":
    contexts.main()
