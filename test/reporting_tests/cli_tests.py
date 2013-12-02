import datetime
import sys
from io import StringIO
from unittest import mock
import sure
import contexts
from contexts import reporting
from .. import tools


# TODO: break up this test
class WhenWatchingForDots:
    def context(self):
        self.stringio = StringIO()
        self.notifier = reporting.shared.ReporterNotifier(reporting.cli.DotsReporter(self.stringio))
        self.fake_context = tools.create_context("context")
        self.fake_assertion = tools.create_assertion("assertion")

    def because_we_run_some_assertions(self):
        # each of these with-stmts should be a separate test case
        with self.notifier.run_suite(tools.create_suite()):
            with self.notifier.run_context(self.fake_context):

                with self.notifier.run_assertion(self.fake_assertion):
                    pass
                self.first = self.stringio.getvalue()

                with self.notifier.run_assertion(self.fake_assertion):
                    pass
                self.second = self.stringio.getvalue()

                with self.notifier.run_assertion(self.fake_assertion):
                    assert False
                self.third = self.stringio.getvalue()

                with self.notifier.run_assertion(self.fake_assertion):
                    raise Exception
                self.fourth = self.stringio.getvalue()

                raise Exception

            self.fifth = self.stringio.getvalue()

            raise tools.FakeException()
        self.sixth = self.stringio.getvalue()

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

    def it_should_print_an_E_for_the_unexpected_error(self):
        self.sixth.should.equal('..FEEE')


# TODO: break up this test
class WhenPrintingVerbosely:
    def context(self):
        self.stringio = StringIO()
        self.notifier = reporting.shared.ReporterNotifier(reporting.cli.VerboseReporter(self.stringio))
        self.outputs = []

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
        # each of these with-stmts should be a separate test case
        with self.notifier.run_suite(None):
            with self.notifier.run_context(self.context1):
                self.outputs.append(self.stringio.getvalue())

                with self.notifier.run_assertion(self.assertion1):
                    pass
                self.outputs.append(self.stringio.getvalue())

                with self.notifier.run_assertion(self.assertion2):
                    raise self.exception2
                self.outputs.append(self.stringio.getvalue())

                with self.notifier.run_assertion(self.assertion3):
                    raise self.exception3
                self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.context2):
                raise self.exception4
            self.outputs.append(self.stringio.getvalue())

            raise self.exception5
        self.outputs.append(self.stringio.getvalue())

    def it_should_say_the_ctx_started(self):
        self.get_output(0).should.equal("made up context 1\n")

    def it_should_say_the_first_assertion_passed(self):
        self.get_output(1).should.equal('  PASS: assertion 1\n')

    def it_should_output_a_stack_trace_for_the_failed_assertion(self):
        self.get_output(2).should.equal(
"""  FAIL: assertion 2
    Traceback (most recent call last):
      File "made_up_file_10.py", line 1, in made_up_function_1
        frame1
      File "made_up_file_11.py", line 2, in made_up_function_2
        frame2
    test.tools.FakeAssertionError: you fail
""")

    def it_should_output_a_stack_trace_for_the_errored_assertion(self):
        self.get_output(3).should.equal(
"""  ERROR: assertion 3
    Traceback (most recent call last):
      File "made_up_file_12.py", line 3, in made_up_function_3
        frame3
      File "made_up_file_13.py", line 4, in made_up_function_4
        frame4
    test.tools.FakeException: no
""")

    def it_should_output_a_stack_trace_for_the_errored_ctx(self):
        self.get_output(4).should.equal(
"""made up context 2 -> ['abc', 123]
  Traceback (most recent call last):
    File "made_up_file_14.py", line 3, in made_up_function_3
      frame3
    File "made_up_file_15.py", line 4, in made_up_function_4
      frame4
  test.tools.FakeException: out
""")

    def it_should_output_a_stack_trace_for_the_unexpected_error_and_a_summary(self):
        self.get_output(5).should.equal(
"""Traceback (most recent call last):
  File "made_up_file_16.py", line 3, in made_up_function_3
    frame3
  File "made_up_file_17.py", line 4, in made_up_function_4
    frame4
test.tools.FakeException: out

----------------------------------------------------------------------
FAILED!
2 contexts, 3 assertions: 1 failed, 3 errors
""")

    def get_output(self, n):
        full_output_n = self.outputs[n]
        return full_output_n[len(self.outputs[n-1]):] if n != 0 else full_output_n


class WhenPrintingASuccessSummary:
    def in_the_context_of_a_successful_run(self):
        self.stringio = StringIO()
        self.notifier = reporting.shared.ReporterNotifier(reporting.cli.SummarisingReporter(self.stringio))
        self.ctx1 = tools.create_context("")
        self.ctx2 = tools.create_context("")
        self.assertion1 = tools.create_assertion("")
        self.assertion2 = tools.create_assertion("")
        self.assertion3 = tools.create_assertion("")

    def because_we_run_some_tests(self):
        with self.notifier.run_suite(tools.create_suite()):
            with self.notifier.run_context(self.ctx1):
                with self.notifier.run_assertion(self.assertion1):
                    pass
                with self.notifier.run_assertion(self.assertion2):
                    pass

            with self.notifier.run_context(self.ctx2):
                with self.notifier.run_assertion(self.assertion2):
                    pass

    def it_should_print_the_summary_to_the_stream(self):
        self.stringio.getvalue().should.equal(
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")


# TODO: break up this test
class WhenPrintingAFailureSummary:
    def in_the_context_of_a_failed_run(self):
        self.stringio = StringIO()
        self.reporter = reporting.shared.ReporterNotifier(reporting.cli.SummarisingReporter(self.stringio))

        self.context1 = tools.create_context("made.up_context_1")

        self.assertion1 = tools.create_assertion("made.up.assertion_1")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception1 = tools.build_fake_exception(tb1, "Gotcha")

        self.assertion2 = tools.create_assertion("made.up.assertion_2")
        tb2 = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
               ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        self.exception2 = tools.build_fake_assertion_error(tb2, "you fail")

        self.assertion3 = tools.create_assertion("made.up.assertion_3")

        self.context2 = tools.create_context("made.up_context_2", ["abc", 123, None])
        tb3 = [('made_up_file_5.py', 1, 'made_up_function_5', 'frame5'),
               ('made_up_file_6.py', 2, 'made_up_function_6', 'frame6')]
        self.exception3 = tools.build_fake_exception(tb3, "oh dear")

        tb4 = [('made_up_file_7.py', 1, 'made_up_function_7', 'frame7'),
               ('made_up_file_8.py', 2, 'made_up_function_8', 'frame8')]
        self.exception4 = tools.build_fake_exception(tb4, "oh dear")

        self.context3 = tools.create_context("made.up_context_3")

    def because_we_run_some_tests(self):
        with self.reporter.run_suite(tools.create_suite()):
            with self.reporter.run_context(self.context1):
                with self.reporter.run_assertion(self.assertion1):
                    raise self.exception1
                with self.reporter.run_assertion(self.assertion2):
                    raise self.exception2
                with self.reporter.run_assertion(self.assertion3):
                    pass

            with self.reporter.run_context(self.context2):
                raise self.exception3

            with self.reporter.run_context(self.context3):
                pass

            self.output_before_end = self.stringio.getvalue()
            raise self.exception4

    def it_should_print_a_traceback_for_each_failure(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
made up context 1
  ERROR: made up assertion 1
    Traceback (most recent call last):
      File "made_up_file.py", line 3, in made_up_function
        frame1
      File "another_made_up_file.py", line 2, in another_made_up_function
        frame2
    test.tools.FakeException: Gotcha
  FAIL: made up assertion 2
    Traceback (most recent call last):
      File "made_up_file_3.py", line 1, in made_up_function_3
        frame3
      File "made_up_file_4.py", line 2, in made_up_function_4
        frame4
    test.tools.FakeAssertionError: you fail
made up context 2 -> ['abc', 123, None]
  Traceback (most recent call last):
    File "made_up_file_5.py", line 1, in made_up_function_5
      frame5
    File "made_up_file_6.py", line 2, in made_up_function_6
      frame6
  test.tools.FakeException: oh dear
Traceback (most recent call last):
  File "made_up_file_7.py", line 1, in made_up_function_7
    frame7
  File "made_up_file_8.py", line 2, in made_up_function_8
    frame8
test.tools.FakeException: oh dear
----------------------------------------------------------------------
FAILED!
3 contexts, 3 assertions: 1 failed, 3 errors
""")

    def it_should_not_print_until_the_end(self):
        self.output_before_end.should.be.empty


# TODO: break up this test
class WhenCapturingStdOut:
    def context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

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
        self.reporter = reporting.shared.ReporterNotifier(reporting.cli.StdOutCapturingReporter(self.stringio))

    def because_we_print_some_stuff(self):
        with self.reporter.run_suite(tools.create_suite()):
            with self.reporter.run_context(self.ctx1):
                print("passing context")
                with self.reporter.run_assertion(self.assertion1):
                    print("passing assertion")
                    print("to stderr", file=sys.stderr)

            with self.reporter.run_context(self.ctx2):
                print("failing context")
                with self.reporter.run_assertion(self.assertion2):
                    print("failing assertion")
                    raise tools.FakeAssertionError()
                with self.reporter.run_assertion(self.assertion3):
                    print("erroring assertion")
                    raise tools.FakeException()

            with self.reporter.run_context(self.ctx3):
                print("erroring context")
                with self.reporter.run_assertion(self.assertion4):
                    print("assertion in erroring context")
                raise tools.FakeException()

            with self.reporter.run_context(self.ctx4):
                with self.reporter.run_assertion(self.assertion5):
                    # don't print anything
                   raise tools.FakeAssertionError()

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
        self.reporter = reporting.shared.ReporterNotifier(reporting.cli.ColouredReporter(self.stringio))
        self.outputs = []

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
        with self.reporter.run_suite(tools.create_suite()):
            with self.reporter.run_context(self.context1):
                self.outputs.append(self.stringio.getvalue())

                with self.reporter.run_assertion(self.assertion1):
                    pass
                self.outputs.append(self.stringio.getvalue())

                with self.reporter.run_assertion(self.assertion2):
                    raise self.exception2
                self.outputs.append(self.stringio.getvalue())

                with self.reporter.run_assertion(self.assertion3):
                    raise self.exception3
                self.outputs.append(self.stringio.getvalue())

            with self.reporter.run_context(self.context2):
                raise self.exception4
            self.outputs.append(self.stringio.getvalue())

            raise self.exception5
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

        self.stringio = StringIO()
        self.reporter = reporting.shared.ReporterNotifier(reporting.cli.TimedReporter(self.stringio))

    def because_we_run_a_suite(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            with self.reporter.run_suite(tools.create_suite()):
                datetime.datetime.now.return_value += self.fake_soon

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
        self.reporter = reporting.shared.make_readable(self.input)

    def it_should_return_a_string_with_appropriate_spaces(self):
        self.reporter.should.equal(self.expected)


if __name__ == "__main__":
    contexts.main()
