import datetime
import sys
from io import StringIO
from unittest import mock
import sure
import contexts
from contexts import reporting
from . import tools


class WhenWatchingForDots(object):
    def context(self):
        self.stringio = StringIO()
        self.reporter = reporting.DotsReporter(self.stringio)
        self.fake_context = tools.create_context("context")
        self.fake_assertion = tools.create_assertion("assertion")

    def because_we_run_some_assertions(self):
        self.reporter.context_started(self.fake_context)

        self.reporter.assertion_started(self.fake_assertion)
        self.reporter.assertion_passed(self.fake_assertion)
        self.first = self.stringio.getvalue()

        self.reporter.assertion_started(self.fake_assertion)
        self.reporter.assertion_passed(self.fake_assertion)
        self.second = self.stringio.getvalue()

        self.reporter.assertion_started(self.fake_assertion)
        self.reporter.assertion_failed(self.fake_assertion, tools.FakeException())
        self.third = self.stringio.getvalue()

        self.reporter.assertion_started(self.fake_assertion)
        self.reporter.assertion_errored(self.fake_assertion, tools.FakeException())
        self.fourth = self.stringio.getvalue()

        self.reporter.context_errored(self.fake_context, tools.FakeException())
        self.fifth = self.stringio.getvalue()

        self.reporter.unexpected_error(tools.FakeException())
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

class WhenPrintingASuccessfulReport(object):
    def in_the_context_of_a_successful_run(self):
        # We don't want it to try and print anything while we set it up
        self.stringio = StringIO()
        self.reporter = reporting.SummarisingReporter(StringIO())

    def because_we_run_some_tests(self):
        self.reporter.suite_started(None)

        self.reporter.context_started(tools.create_context(""))
        self.reporter.assertion_started(tools.create_assertion(""))
        self.reporter.assertion_passed(tools.create_assertion(""))
        self.reporter.assertion_started(tools.create_assertion(""))
        self.reporter.assertion_passed(tools.create_assertion(""))
        self.reporter.context_ended(tools.create_context(""))

        self.reporter.context_started(tools.create_context(""))
        self.reporter.assertion_started(tools.create_assertion(""))
        self.reporter.assertion_passed(tools.create_assertion(""))
        self.reporter.context_ended(tools.create_context(""))

        self.reporter.stream = self.stringio
        self.reporter.suite_ended(None)

    def it_should_print_the_summary_to_the_stream(self):
        self.stringio.getvalue().should.equal(
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")

class WhenPrintingAFailureReport(object):
    def in_the_context_of_a_failed_run(self):
        self.reporter = reporting.SummarisingReporter(StringIO())
        self.stringio = StringIO()

        self.context1 = tools.create_context("made.up_context_1")

        self.assertion1 = tools.create_assertion("made.up.assertion_1")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception1 = tools.build_fake_exception(tb1, "Gotcha")

        self.assertion2 = tools.create_assertion("made.up.assertion_2")
        tb2 = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
               ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        self.exception2 = tools.build_fake_exception(tb2, "you fail")

        self.assertion3 = tools.create_assertion("made.up.assertion_3")

        self.context2 = tools.create_context("made.up_context_2", ["abc", 123, None])
        tb3 = [('made_up_file_5.py', 1, 'made_up_function_5', 'frame5'),
               ('made_up_file_6.py', 2, 'made_up_function_6', 'frame6')]
        self.exception3 = tools.build_fake_exception(tb3, "oh dear")
        
        tb4 = [('made_up_file_7.py', 1, 'made_up_function_7', 'frame7'),
               ('made_up_file_8.py', 2, 'made_up_function_8', 'frame8')]
        self.exception4 = tools.build_fake_exception(tb4, "oh dear")

    def because_we_run_some_tests(self):
        self.reporter.suite_started(None)

        self.reporter.context_started(self.context1)
        self.reporter.assertion_started(self.assertion1)
        self.reporter.assertion_errored(self.assertion1, self.exception1)
        self.reporter.assertion_started(self.assertion2)
        self.reporter.assertion_failed(self.assertion2, self.exception2)
        self.reporter.assertion_started(self.assertion3)
        self.reporter.assertion_passed(self.assertion3)
        self.reporter.context_ended(self.context1)

        self.reporter.context_started(self.context2)
        self.reporter.context_errored(self.context2, self.exception3)

        self.reporter.context_started(tools.create_context("made.up_context_3"))
        self.reporter.context_ended(tools.create_context("made.up_context_3"))

        self.reporter.unexpected_error(self.exception4)

        self.reporter.stream = self.stringio
        self.reporter.suite_ended(None)

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
    test.tools.FakeException: you fail
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

class WhenCapturingStdOut(object):
    def context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

        self.fake_context = tools.create_context("context")
        self.fake_assertion = tools.create_assertion("assertion")

        self.stringio = StringIO()
        # we don't want the output to be cluttered up with dots
        self.reporter = reporting.StdOutCapturingReporter(StringIO())

    def because_we_print_some_stuff(self):
        self.reporter.suite_started(None)

        self.reporter.context_started(self.fake_context)
        print("passing context")
        self.reporter.assertion_started(self.fake_assertion)
        print("passing assertion")
        print("to stderr", file=sys.stderr)
        self.reporter.assertion_passed(self.fake_assertion)
        self.reporter.context_ended(self.fake_context)

        self.reporter.context_started(self.fake_context)
        print("failing context")
        self.reporter.assertion_started(self.fake_assertion)
        print("failing assertion")
        self.reporter.assertion_failed(self.fake_assertion, tools.FakeException())
        self.reporter.assertion_started(self.fake_assertion)
        print("erroring assertion")
        self.reporter.assertion_errored(self.fake_assertion, tools.FakeException())
        self.reporter.context_ended(self.fake_context)

        self.reporter.context_started(self.fake_context)
        print("erroring context")
        self.reporter.assertion_started(self.fake_assertion)
        print("assertion in erroring context")
        self.reporter.assertion_passed(self.fake_assertion)
        self.reporter.context_errored(self.fake_context, tools.FakeException())

        self.reporter.context_started(self.fake_context)
        self.reporter.assertion_started(self.fake_assertion)
        # don't print anything
        self.reporter.assertion_failed(self.fake_assertion, tools.FakeException())
        self.reporter.context_ended(self.fake_context)

        self.reporter.stream = self.stringio
        self.reporter.suite_ended(None)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_let_stderr_through(self):
        self.fake_stderr.getvalue().should.equal("to stderr\n")

    def it_should_output_the_captured_stdout_for_the_failures(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
context
  FAIL: assertion
    test.tools.FakeException
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
    test.tools.FakeException
----------------------------------------------------------------------
FAILED!
4 contexts, 5 assertions: 2 failed, 2 errors
""")

    def cleanup_stdout_and_stderr(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

class WhenTimingATestRun(object):
    def context(self):
        self.fake_now = datetime.datetime(2013, 10, 22, 13, 41, 0)
        self.fake_soon = datetime.timedelta(seconds=10, milliseconds=490)

        class FakeDateTime(datetime.datetime):
            now = mock.Mock(return_value=self.fake_now)
        self.FakeDateTime = FakeDateTime

        self.stringio = StringIO()
        self.reporter = reporting.TimedReporter(self.stringio)

    def because_we_run_a_suite(self):
        with mock.patch('datetime.datetime', self.FakeDateTime):
            self.reporter.suite_started(None)
            datetime.datetime.now.return_value += self.fake_soon
            self.reporter.suite_ended(None)

    def it_should_report_the_total_time_for_the_test_run(self):
        self.stringio.getvalue().should.equal("(10.5 seconds)\n")


class WhenRunningInTeamCity(object):
    def context(self):
        self.stringio = StringIO()

        self.mock_escape = mock.Mock(side_effect=reporting.TeamCityReporter.teamcity_escape)
        reporting.TeamCityReporter.teamcity_escape = self.mock_escape

        self.reporter = reporting.TeamCityReporter(self.stringio)

        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception1 = tools.build_fake_exception(tb1, "Gotcha")
        self.formatted_tb1 = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'test.tools.FakeException: Gotcha')

        tb2 = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
               ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        self.exception2 = tools.build_fake_exception(tb2, "you fail")
        self.formatted_tb2 = (
'Traceback (most recent call last):|n'
'  File "made_up_file_3.py", line 1, in made_up_function_3|n'
'    frame3|n'
'  File "made_up_file_4.py", line 2, in made_up_function_4|n'
'    frame4|n'
'test.tools.FakeException: you fail')

        tb3 = [('made_up_file_5.py', 1, 'made_up_function_5', 'frame5'),
               ('made_up_file_6.py', 2, 'made_up_function_6', 'frame6')]
        self.exception3 = tools.build_fake_exception(tb3, "oh dear")
        self.formatted_tb3 = (
'Traceback (most recent call last):|n'
'  File "made_up_file_5.py", line 1, in made_up_function_5|n'
'    frame5|n'
'  File "made_up_file_6.py", line 2, in made_up_function_6|n'
'    frame6|n'
'test.tools.FakeException: oh dear')
        tb4 = [('made_up_file_7.py', 1, 'made_up_function_7', 'frame7'),
               ('made_up_file_8.py', 2, 'made_up_function_8', 'frame8')]
        self.exception4 = tools.build_fake_exception(tb4, "another exception")
        self.formatted_tb4 = (
'Traceback (most recent call last):|n'
'  File "made_up_file_7.py", line 1, in made_up_function_7|n'
'    frame7|n'
'  File "made_up_file_8.py", line 2, in made_up_function_8|n'
'    frame8|n'
'test.tools.FakeException: another exception')

        self.outputs = []

    def because_we_run_some_assertions(self):
        self.reporter.suite_started(None)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.context_started(tools.create_context("FakeContext"))

        self.reporter.assertion_started(tools.create_assertion("FakeAssertion1"))
        self.outputs.append(self.stringio.getvalue())
        self.reporter.assertion_passed(tools.create_assertion("FakeAssertion1"))
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(tools.create_assertion("FakeAssertion2"))
        self.outputs.append(self.stringio.getvalue())
        self.reporter.assertion_passed(tools.create_assertion("FakeAssertion2"))
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(tools.create_assertion("FakeAssertion3"))
        self.outputs.append(self.stringio.getvalue())
        self.reporter.assertion_failed(tools.create_assertion("FakeAssertion3"), self.exception1)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.assertion_started(tools.create_assertion("FakeAssertion4"))
        self.outputs.append(self.stringio.getvalue())
        self.reporter.assertion_errored(tools.create_assertion("FakeAssertion4"), self.exception2)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.context_errored(tools.create_context("FakeContext"), self.exception3)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.context_started(tools.create_context("FakeContext2", ["abc", 123, None]))
        self.reporter.assertion_started(tools.create_assertion("FakeAssertion5"))
        self.reporter.assertion_passed(tools.create_assertion("FakeAssertion5"))
        self.reporter.context_ended(tools.create_context("FakeContext2", ["abc", 123, None]))
        self.outputs.append(self.stringio.getvalue())

        self.reporter.unexpected_error(self.exception4)
        self.outputs.append(self.stringio.getvalue())

        self.reporter.suite_ended(None)
        self.outputs.append(self.stringio.getvalue())

    def it_should_call_escape_for_every_object_it_formats(self):
        self.mock_escape.mock_calls.should.have.length_of(25)

    def it_should_tell_team_city_it_started(self):
        self.get_output(0,0).should.equal("##teamcity[testSuiteStarted name='contexts']")
    def it_should_not_report_anything_else_at_start(self):
        self.get_output.when.called_with(0,1).should.throw(IndexError)

    def it_should_tell_team_city_the_first_assertion_started(self):
        self.get_output(1,1).should.equal("##teamcity[testStarted name='Fake context -> Fake assertion 1']")
    def it_should_not_report_anything_else_at_first_assertion_start(self):
        self.get_output.when.called_with(1,2).should.throw(IndexError)
    def it_should_tell_team_city_the_first_assertion_passed(self):
        self.get_output(2,2).should.equal("##teamcity[testFinished name='Fake context -> Fake assertion 1']")
    def it_should_not_report_anything_else_at_first_assertion_end(self):
        self.get_output.when.called_with(2,3).should.throw(IndexError)

    def it_should_tell_team_city_the_second_assertion_started(self):
        self.get_output(3,3).should.equal("##teamcity[testStarted name='Fake context -> Fake assertion 2']")
    def it_should_not_report_anything_else_at_second_assertion_start(self):
        self.get_output.when.called_with(3,4).should.throw(IndexError)
    def it_should_tell_team_city_the_second_assertion_passed(self):
        self.get_output(4,4).should.equal("##teamcity[testFinished name='Fake context -> Fake assertion 2']")
    def it_should_not_report_anything_else_at_second_assertion_end(self):
        self.get_output.when.called_with(4,5).should.throw(IndexError)

    def it_should_tell_team_city_the_third_assertion_started(self):
        self.get_output(5,5).should.equal("##teamcity[testStarted name='Fake context -> Fake assertion 3']")
    def it_should_not_report_anything_else_at_third_assertion_start(self):
        self.get_output.when.called_with(5,6).should.throw(IndexError)
    def it_should_output_a_stack_trace_for_the_third_assertion(self):
        self.get_output(6,6).should.equal("##teamcity[testFailed name='Fake context -> Fake assertion 3' message='Gotcha' details='{}']".format(self.formatted_tb1))
        self.get_output(6,7).should.equal("##teamcity[testFinished name='Fake context -> Fake assertion 3']")
    def it_should_not_report_anything_else_at_third_assertion_end(self):
        self.get_output.when.called_with(6,8).should.throw(IndexError)

    def it_should_tell_team_city_the_fourth_assertion_started(self):
        self.get_output(7,8).should.equal("##teamcity[testStarted name='Fake context -> Fake assertion 4']")
    def it_should_not_report_anything_else_at_fourth_assertion_start(self):
        self.get_output.when.called_with(7,9).should.throw(IndexError)
    def it_should_output_a_stack_trace_for_the_fourth_assertion(self):
        self.get_output(8,9).should.equal("##teamcity[testFailed name='Fake context -> Fake assertion 4' message='you fail' details='{}']".format(self.formatted_tb2))
        self.get_output(8,10).should.equal("##teamcity[testFinished name='Fake context -> Fake assertion 4']")
    def it_should_not_report_anything_else_at_fourth_assertion_end(self):
        self.get_output.when.called_with(8,11).should.throw(IndexError)

    def it_should_tell_team_city_another_test_started_and_failed_for_the_ctx_error(self):
        self.get_output(9,11).should.equal("##teamcity[testStarted name='Fake context']")
        self.get_output(9,12).should.equal("##teamcity[testFailed name='Fake context' message='oh dear' details='{}']".format(self.formatted_tb3))
        self.get_output(9,13).should.equal("##teamcity[testFinished name='Fake context']")
    def it_should_not_report_anything_else_following_the_ctx_error(self):
        self.get_output.when.called_with(9,14).should.throw(IndexError)

    def it_should_report_the_exmpl(self):
        self.get_output(10,14).should.equal("##teamcity[testStarted name='Fake context 2 -> |[|'abc|', 123, None|] -> Fake assertion 5']")
        self.get_output(10,15).should.equal("##teamcity[testFinished name='Fake context 2 -> |[|'abc|', 123, None|] -> Fake assertion 5']")
    def it_should_not_report_anything_following_the_second_ctx(self):
        self.get_output.when.called_with(10,16).should.throw(IndexError)

    def it_should_tell_team_city_another_test_started_and_failed_for_the_unexpected_error(self):
        self.get_output(11,16).should.equal("##teamcity[testStarted name='Test error']")
        self.get_output(11,17).should.equal("##teamcity[testFailed name='Test error' message='another exception' details='{}']".format(self.formatted_tb4))
        self.get_output(11,18).should.equal("##teamcity[testFinished name='Test error']")
    def it_should_not_report_anything_else_following_unexpected_error(self):
        self.get_output.when.called_with(11,19).should.throw(IndexError)

    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(12, 19).should.equal("##teamcity[testSuiteFinished name='contexts']")
    def it_should_not_report_anything_else_at_suite_end(self):
        self.get_output.when.called_with(12,20).should.throw(IndexError)

    def cleanup_the_mock(self):
        reporting.TeamCityReporter.teamcity_escape = self.mock_escape.return_value

    def get_output(self, n, m):
        return self.outputs[n].strip().split('\n')[m]

class WhenEscapingForTeamCity(object):
    def because_we_escape_a_string(self):
        # unicode replacement not supported yet
        self.reporter = reporting.TeamCityReporter.teamcity_escape("'\n\r|[]")
    def it_should_escape_the_chars_correctly(self):
        self.reporter.should.equal("|'|n|r|||[|]")

class WhenMakingANameHumanReadable(object):
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
        self.reporter = reporting.make_readable(self.input)

    def it_should_return_a_string_with_appropriate_spaces(self, example):
        self.reporter.should.equal(self.expected)

if __name__ == "__main__":
    contexts.main()
