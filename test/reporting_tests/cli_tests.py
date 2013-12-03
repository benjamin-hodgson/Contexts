import datetime
import sys
from io import StringIO
from unittest import mock
import sure
import contexts
from contexts import reporting
from .. import tools


class WhenPrintingASuccessSummary:
    def in_the_context_of_a_successful_run(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.SummarisingReporter(self.stringio)

        self.ctx1 = tools.create_context("")
        self.ctx2 = tools.create_context("")
        self.assertion1 = tools.create_assertion("")
        self.assertion2 = tools.create_assertion("")
        self.assertion3 = tools.create_assertion("")

        self.reporter.context_started(self.ctx1)
        self.reporter.assertion_started(self.assertion1)
        self.reporter.assertion_passed(self.assertion1)
        self.reporter.assertion_started(self.assertion2)
        self.reporter.assertion_passed(self.assertion2)
        self.reporter.context_ended(self.ctx1)

        self.reporter.context_started(self.ctx2)
        self.reporter.assertion_started(self.assertion3)
        self.reporter.assertion_passed(self.assertion3)
        self.reporter.context_ended(self.ctx2)

    def because_the_suite_ends(self):
        self.reporter.suite_ended(tools.create_suite())

    def it_should_print_the_summary_to_the_stream(self):
        self.stringio.getvalue().should.equal(
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")


class WhenPrintingAFailureSummary:
    def establish_that_some_tests_have_failed(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.SummarisingReporter(self.stringio)

        self.context = tools.create_context("made.up_context")
        self.assertion = tools.create_assertion("made.up.assertion_1")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb1, "Gotcha")

        self.reporter.context_started(self.context)
        self.reporter.assertion_started(self.assertion)
        self.reporter.assertion_failed(self.assertion, self.exception)
        self.reporter.context_ended(self.context)

    def because_the_suite_ends(self):
        self.reporter.suite_ended(tools.create_suite)

    def it_should_print_the_failure_tracebacks(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
made up context
  FAIL: made up assertion 1
    Traceback (most recent call last):
      File "made_up_file.py", line 3, in made_up_function
        frame1
      File "another_made_up_file.py", line 2, in another_made_up_function
        frame2
    test.tools.FakeAssertionError: Gotcha
----------------------------------------------------------------------
FAILED!
1 context, 1 assertion: 1 failed, 0 errors
""")


# TODO: break up this test
class WhenCapturingStdOut:
    def context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

        self.suite = tools.create_suite()
        self.ctx1 = tools.create_context("context")
        self.ctx2 = tools.create_context("context")
        self.ctx3 = tools.create_context("context")
        self.ctx4 = tools.create_context("context")
        self.assertion1 = tools.create_assertion("assertion")
        self.assertion2 = tools.create_assertion("assertion")
        self.assertion3 = tools.create_assertion("assertion")
        self.assertion4 = tools.create_assertion("assertion")
        self.assertion5 = tools.create_assertion("assertion")

        self.stringio = StringIO()
        self.reporter = reporting.cli.StdOutCapturingReporter(self.stringio)

    def because_we_print_some_stuff(self):
        self.reporter.suite_started(self.suite)
        self.reporter.context_started(self.ctx1)
        print("passing context")
        self.reporter.assertion_started(self.assertion1)
        print("passing assertion")
        print("to stderr", file=sys.stderr)
        self.reporter.assertion_passed(self.assertion1)
        self.reporter.context_ended(self.ctx1)

        self.reporter.context_started(self.ctx2)
        print("failing context")
        self.reporter.assertion_started(self.assertion2)
        print("failing assertion")
        self.reporter.assertion_failed(self.assertion2, tools.FakeAssertionError())
        self.reporter.assertion_started(self.assertion3)
        print("erroring assertion")
        self.reporter.assertion_errored(self.assertion3, tools.FakeException())
        self.reporter.context_ended(self.ctx2)

        self.reporter.context_started(self.ctx3)
        print("erroring context")
        self.reporter.assertion_started(self.assertion4)
        print("assertion in erroring context")
        self.reporter.assertion_passed(self.assertion4)
        self.reporter.context_errored(self.ctx3, tools.FakeException())

        self.reporter.context_started(self.ctx4)
        self.reporter.assertion_started(self.assertion5)
        # don't print anything
        self.reporter.assertion_failed(self.assertion5, tools.FakeAssertionError())
        self.reporter.context_ended(self.ctx4)

        self.reporter.suite_ended(self.suite)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_let_stderr_through(self):
        self.fake_stderr.getvalue().should.equal("to stderr\n")

    def it_should_output_the_captured_stdout_for_the_failures(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
context
  FAIL: assertion
    test.tools.FakeAssertionError
    ------------------ >> begin captured stdout << -------------------
    failing context
    failing assertion
    ------------------- >> end captured stdout << --------------------
  ERROR: assertion
    test.tools.FakeException
    ------------------ >> begin captured stdout << -------------------
    failing context
    failing assertion
    erroring assertion
    ------------------- >> end captured stdout << --------------------
context
  test.tools.FakeException
  ------------------- >> begin captured stdout << --------------------
  erroring context
  assertion in erroring context
  -------------------- >> end captured stdout << ---------------------
context
  FAIL: assertion
    test.tools.FakeAssertionError
----------------------------------------------------------------------
FAILED!
4 contexts, 5 assertions: 2 failed, 2 errors
""")

    def cleanup_stdout_and_stderr(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr


class WhenColouringOutput:
    def context(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.ColouredReporter(self.stringio)
        self.outputs = []

        self.suite = tools.create_suite()
        self.context1 = tools.create_context("made.up_context_1")

        self.assertion1 = tools.create_assertion("assertion1")

        self.assertion2 = tools.create_assertion("assertion2")
        tb2 = [('made_up_file_10.py', 1, 'made_up_function_1', 'frame1'),
               ('made_up_file_11.py', 2, 'made_up_function_2', 'frame2')]
        self.exception2 = tools.build_fake_assertion_error(tb2, "you fail")

        self.assertion3 = tools.create_assertion("assertion3")
        tb3 = [('made_up_file_12.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_13.py', 4, 'made_up_function_4', 'frame4')]
        self.exception3 = tools.build_fake_exception(tb3, "no")

        tb4 = [('made_up_file_14.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_15.py', 4, 'made_up_function_4', 'frame4')]
        self.exception4 = tools.build_fake_exception(tb4, "out")

        tb5 = [('made_up_file_16.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_17.py', 4, 'made_up_function_4', 'frame4')]
        self.exception5 = tools.build_fake_exception(tb5, "out")

        self.context2 = tools.create_context("made.up_context_2", ["abc", 123])

    def because_we_run_some_tests(self):
        self.reporter.suite_started(self.suite)
        self.reporter.context_started(self.context1)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(self.assertion1)
        self.reporter.assertion_passed(self.assertion1)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(self.assertion2)
        self.reporter.assertion_failed(self.assertion2, self.exception2)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(self.assertion3)
        self.reporter.assertion_errored(self.assertion3, self.exception3)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.context_ended(self.context1)

        self.reporter.context_started(self.context2)
        self.reporter.context_errored(self.context2, self.exception4)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.unexpected_error(self.exception5)
        self.reporter.suite_ended(self.suite)
        self.outputs.append(self.stringio.getvalue())

    def it_should_say_the_ctx_started(self):
        self.get_output(0).should.equal("made up context 1\n")

    def it_should_output_in_green_for_the_passing_assertion(self):
        self.get_output(1).should.equal('\x1b[32m  PASS: assertion 1\n\x1b[39m')

    def it_should_output_a_red_stack_trace_for_the_failed_assertion(self):
        self.get_output(2).should.equal(
"""\x1b[31m  FAIL: assertion 2
    Traceback (most recent call last):
      File "made_up_file_10.py", line 1, in made_up_function_1
        frame1
      File "made_up_file_11.py", line 2, in made_up_function_2
        frame2
    test.tools.FakeAssertionError: you fail
\x1b[39m""")

    def it_should_output_a_red_stack_trace_for_the_errored_assertion(self):
        self.get_output(3).should.equal(
"""\x1b[31m  ERROR: assertion 3
    Traceback (most recent call last):
      File "made_up_file_12.py", line 3, in made_up_function_3
        frame3
      File "made_up_file_13.py", line 4, in made_up_function_4
        frame4
    test.tools.FakeException: no
\x1b[39m""")

    def it_should_output_a_red_stack_trace_for_the_errored_ctx(self):
        self.get_output(4).should.equal(
"""made up context 2 -> ['abc', 123]
\x1b[31m  Traceback (most recent call last):
    File "made_up_file_14.py", line 3, in made_up_function_3
      frame3
    File "made_up_file_15.py", line 4, in made_up_function_4
      frame4
  test.tools.FakeException: out
\x1b[39m""")

    def it_should_output_a_red_stack_trace_for_the_unexpected_error(self):
        self.get_output(5).should.equal(
"""\x1b[31mTraceback (most recent call last):
  File "made_up_file_16.py", line 3, in made_up_function_3
    frame3
  File "made_up_file_17.py", line 4, in made_up_function_4
    frame4
test.tools.FakeException: out
\x1b[39m
----------------------------------------------------------------------
FAILED!
2 contexts, 3 assertions: 1 failed, 3 errors
""")

    def get_output(self, n):
        full_output_n = self.outputs[n]
        return full_output_n[len(self.outputs[n-1]):] if n != 0 else full_output_n


class WhenTimingATestRun:
    def context(self):
        self.fake_now = datetime.datetime(2013, 10, 22, 13, 41, 0)
        self.fake_soon = datetime.timedelta(seconds=10, milliseconds=490)

        class FakeDateTime(datetime.datetime):
            now = mock.Mock(return_value=self.fake_now)
        self.FakeDateTime = FakeDateTime

        self.suite = tools.create_suite()
        self.stringio = StringIO()
        self.reporter = reporting.cli.TimedReporter(self.stringio)

    def because_we_run_a_suite(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            self.reporter.suite_started(self.suite)
            datetime.datetime.now.return_value += self.fake_soon
            self.reporter.suite_ended(self.suite)

    def it_should_report_the_total_time_for_the_test_run(self):
        self.stringio.getvalue().should.equal("(10.5 seconds)\n")


class WhenMakingANameHumanReadable:
    @classmethod
    def examples(self):
        yield "lowercase", "lowercase"
        yield "Capitalised", "Capitalised"
        yield "snake_case_name", "snake case name"
        yield "Camel_Snake_Case", "Camel snake case"
        yield "CamelCase", "Camel case"
        yield "HTML", "HTML"
        yield "HTMLParser", "HTML parser"
        yield "SimpleHTTPServer", "Simple HTTP server"
        yield "November2013", "November 2013"
        yield "ABC123", "ABC 123"
        yield "BMW4Series", "BMW 4 series"
        yield "lowerAtStart", "lower at start"
        yield "has.dots.in.the.name", "has dots in the name"
        yield "CamelCaseWithASingleLetterWord", "Camel case with a single letter word"
        yield "Does.EverythingAT_once.TOBe100Percent_Certain", "Does everything AT once TO be 100 percent certain"

    def context(self, example):
        self.input, self.expected = example

    def because_we_make_the_string_readable(self):
        self.result = reporting.shared.make_readable(self.input)

    def it_should_return_a_string_with_appropriate_spaces(self):
        self.result.should.equal(self.expected)


if __name__ == "__main__":
    contexts.main()
