import sys
from io import StringIO
import re
import contexts
from contexts.plugins import teamcity
from contexts.plugins.decorators import setup, action, assertion
from . import tools


class TeamCitySharedContext:
    def shared_context(self):
        self.stringio = StringIO()
        self.reporter = teamcity.TeamCityReporter(self.stringio)
        self.outputs = []

    def parse_line(self, n):
        if n < 0:  # to hide the fact that the last line will be empty
            n -= 1
        return teamcity_parse(self.stringio.getvalue().split('\n')[n])


###########################################################
# Suite tests
###########################################################

class WhenASuiteStartsInTeamCity(TeamCitySharedContext):
    def context(self):
        self.suite_name = 'test_suite'
    def because_the_suite_starts(self):
        self.reporter.suite_started(self.suite_name)
    def it_should_tell_team_city_the_suite_started(self):
        assert teamcity_parse(self.stringio.getvalue()) == ("testSuiteStarted", {'name':self.suite_name})


class WhenASuiteEndsInTeamCity(TeamCitySharedContext):
    def context(self):
        self.suite_name = 'mah_suite'
    def because_the_suite_ends(self):
        self.reporter.suite_ended(self.suite_name)
    def it_should_tell_team_city_the_suite_ended(self):
        assert teamcity_parse(self.stringio.getvalue()) == ("testSuiteFinished", {'name':self.suite_name})


###########################################################
# assertion_started tests
###########################################################

class WhenAnAssertionStartsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('MyNiceContext')
        self.reporter.context_started(context.name, context.example)

    def because_the_assertion_starts(self):
        self.reporter.assertion_started('aLovelyAssertion')

    def it_should_tell_team_city_it_started(self):
        assert self.parse_line(0) == ("testStarted", {'name':'My nice context -> a lovely assertion'})


class WhenAnAssertionInAContextWithExamplesStartsInTeamCity(TeamCitySharedContext):
    @setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.reporter.context_started(context.name, context.example)

    def because_the_assertion_starts(self):
        self.reporter.assertion_started('aLovelyAssertion')

    @assertion
    def it_should_report_the_example(self):
        assert self.parse_line(0)[1]['name'] == 'Context with examples -> 12.3 -> a lovely assertion'


###########################################################
# assertion_passed tests
###########################################################

class WhenAnAssertionPassesInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('MyNiceContext')
        self.reporter.context_started(context.name, context.example)
    def because_the_assertion_ends(self):
        self.reporter.assertion_passed('aLovelyAssertion')
    def it_should_tell_team_city_it_passed(self):
        assert self.parse_line(0) == ("testFinished", {'name':'My nice context -> a lovely assertion'})


class WhenAnAssertionInAContextWithExamplesPassesInTeamCity(TeamCitySharedContext):
    @setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.reporter.context_started(context.name, context.example)
    def because_the_assertion_passes(self):
        self.reporter.assertion_passed('aLovelyAssertion')
    @assertion
    def it_should_report_the_example(self):
        assert self.parse_line(0)[1]['name'] == 'Context with examples -> 12.3 -> a lovely assertion'


class WhenSomethingGetsPrintedDuringAPassingAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        context = tools.create_context('Context')

        self.reporter.context_started(context.name, context.example)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_the_assertion_passes(self):
        self.reporter.assertion_passed('assertion')

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''
    def it_should_not_print_anything_to_stderr(self):
        assert self.fake_stderr.getvalue() == ''

    def it_should_report_what_went_to_stdout(self):
        assert self.parse_line(0) == ("testStdOut", {'name':'Context -> assertion', 'out':'to stdout|n'})
    def it_should_report_what_went_to_stderr(self):
        assert self.parse_line(1) == ("testStdErr", {'name':'Context -> assertion', 'out':'to stderr|n'})

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# assertion_failed tests
###########################################################

class WhenAnAssertionFailsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('FakeContext')

        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "Gotcha")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'plugin_tests.tools.FakeAssertionError: Gotcha')

        self.reporter.context_started(context.name, context.example)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed('Fake_assertion', self.exception)

    def it_should_tell_team_city_it_failed(self):
        assert self.parse_line(0) == (
            "testFailed",
            {
                'name':'Fake context -> Fake assertion',
                'message':'plugin_tests.tools.FakeAssertionError: Gotcha',
                'details':self.formatted_tb
            })
    def it_should_tell_team_city_it_finished(self):
        assert self.parse_line(1) == ("testFinished", {'name':'Fake context -> Fake assertion'})


class WhenAnAssertionInAContextWithExamplesFailsInTeamCity(TeamCitySharedContext):
    @setup
    def establish_that_a_context_with_an_example_is_running(self):
        self.reporter.context_started('ContextWithExamples', 12.3)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed('aLovelyAssertion', Exception())

    @assertion
    def it_should_report_the_example(self):
        assert self.parse_line(0)[1]['name'] == 'Context with examples -> 12.3 -> a lovely assertion'


class WhenSomethingGetsPrintedDuringAFailingAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        context = tools.create_context()
        self.reporter.context_started(context.name, context.example)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed('assertion', Exception())

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''
    def it_should_not_print_anything_to_stderr(self):
        assert self.fake_stderr.getvalue() == ''

    def it_should_report_what_went_to_stdout(self):
        assert self.parse_line(0) == ("testStdOut", {'name':'context -> assertion', 'out':'to stdout|n'})
    def it_should_report_what_went_to_stderr(self):
        assert self.parse_line(1) == ("testStdErr", {'name':'context -> assertion', 'out':'to stderr|n'})

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# assertion_errored tests
###########################################################

class WhenAnAssertionErrorsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('FakeContext')

        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "Gotcha")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'plugin_tests.tools.FakeAssertionError: Gotcha')

        self.reporter.context_started(context.name, context.example)

    def because_the_assertion_errors(self):
        self.reporter.assertion_errored('Fake_assertion', self.exception)

    def it_should_tell_team_city_it_failed(self):
        assert self.parse_line(0) == (
            "testFailed",
            {
                'name':'Fake context -> Fake assertion',
                'message':'plugin_tests.tools.FakeAssertionError: Gotcha',
                'details':self.formatted_tb
            })
    def it_should_tell_team_city_it_finished(self):
        assert self.parse_line(1) == ("testFinished", {'name':'Fake context -> Fake assertion'})


class WhenAnAssertionInAContextWithExamplesErrorsInTeamCity(TeamCitySharedContext):
    @setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)

        self.reporter.context_started(context.name, context.example)

    def because_the_assertion_errors(self):
        self.reporter.assertion_errored('aLovelyAssertion', Exception())

    @assertion
    def it_should_report_the_example(self):
        assert self.parse_line(0)[1]['name'] == 'Context with examples -> 12.3 -> a lovely assertion'


class WhenSomethingGetsPrintedDuringAnErroringAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        self.context = tools.create_context("FakeContext")

        self.reporter.context_started(self.context.name, self.context.example)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_we_run_an_assertion(self):
        self.reporter.assertion_errored("FakeAssertion4", Exception())

    def it_should_not_print_anything_to_the_real_stdout(self):
        assert self.fake_stdout.getvalue() == ''
    def it_should_not_print_anything_to_the_real_stderr(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_tell_team_city_what_went_to_stdout(self):
        assert self.parse_line(0) == ("testStdOut", {'name':'Fake context -> Fake assertion 4', 'out':'to stdout|n'})
    def it_should_tell_team_city_what_went_to_stderr(self):
        assert self.parse_line(1) == ("testStdErr", {'name':'Fake context -> Fake assertion 4', 'out':'to stderr|n'})

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# context_errored tests
###########################################################

class WhenAContextErrorsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        self.context = tools.create_context('FakeContext')

        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_exception(tb, "Gotcha")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'plugin_tests.tools.FakeException: Gotcha')

        self.reporter.context_started(self.context.name, self.context.example)

    def because_we_run_an_assertion(self):
        self.reporter.context_errored(self.context.name, self.context.example, self.exception)

    def it_should_tell_team_city_a_test_started(self):
        assert self.parse_line(0) == ("testStarted", {'name':'Fake context'})
    def it_should_tell_team_city_the_test_failed(self):
        assert self.parse_line(1) == (
            "testFailed",
            {
                'name':'Fake context',
                'message':'plugin_tests.tools.FakeException: Gotcha',
                'details':self.formatted_tb
            })
    def it_should_tell_team_city_the_test_finished(self):
        assert self.parse_line(2) == ("testFinished", {'name':'Fake context'})


class WhenAContextWithExamplesErrorsInTeamCity(TeamCitySharedContext):
    @setup
    def establish_that_a_context_with_an_example_is_running(self):
        self.context = tools.create_context('ContextWithExamples', 12.3)
        self.reporter.context_started(self.context.name, self.context.example)

    @action
    def because_the_context_errors(self):
        self.reporter.context_errored(self.context.name, self.context.example, Exception())

    @assertion
    def it_should_report_the_example(self):
        assert self.parse_line(0)[1]['name'] == 'Context with examples -> 12.3'


class WhenSomethingGetsPrintedDuringAnErroringContextInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        self.context = tools.create_context("FakeContext")

        self.reporter.context_started(self.context.name, self.context.example)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_we_run_an_assertion(self):
        self.reporter.context_errored(self.context.name, self.context.example, Exception())

    def it_should_not_print_anything_to_the_real_stdout(self):
        assert self.fake_stdout.getvalue() == ''
    def it_should_not_print_anything_to_the_real_stderr(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_tell_team_city_what_went_to_stdout(self):
        assert self.parse_line(1) == ("testStdOut", {'name':'Fake context', 'out':'to stdout|n'})
    def it_should_tell_team_city_what_went_to_stderr(self):
        assert self.parse_line(2) == ("testStdErr", {'name':'Fake context', 'out':'to stderr|n'})

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# unexpected_error tests
###########################################################

class WhenAnUnexpectedErrorOccursInTeamCity(TeamCitySharedContext):
    def establish_the_exception(self):
        tb = [('made_up_file_7.py', 1, 'made_up_function_7', 'frame7'),
               ('made_up_file_8.py', 2, 'made_up_function_8', 'frame8')]
        self.exception = tools.build_fake_exception(tb, "another exception")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file_7.py", line 1, in made_up_function_7|n'
'    frame7|n'
'  File "made_up_file_8.py", line 2, in made_up_function_8|n'
'    frame8|n'
'plugin_tests.tools.FakeException: another exception')

    def because_an_unexpected_error_occurs(self):
        self.reporter.unexpected_error(self.exception)

    def it_should_tell_team_city_a_test_started(self):
        assert self.parse_line(0) == ("testStarted", {'name':'Test error'})
    def it_should_tell_team_city_the_test_failed(self):
        assert self.parse_line(1) == (
            "testFailed",
            {
                'name':'Test error',
                'message':'plugin_tests.tools.FakeException: another exception',
                'details':self.formatted_tb
            })
    def it_should_tell_team_city_the_test_finished(self):
        assert self.parse_line(2) == ("testFinished", {'name':'Test error'})


###########################################################
# tests for sequential calls
###########################################################
# these are really testing context_ended and context_errored,
# but sadly we can only observe it through assertion_started

class WhenASecondContextRuns(TeamCitySharedContext):
    def establish_that_a_context_has_run_and_ended(self):
        context1 = tools.create_context('the_first_context')

        self.reporter.context_started(context1.name, context1.example)
        self.reporter.context_ended(context1.name, context1.example)

        self.context2 = tools.create_context('the_second_context')

        self.reporter.context_started(self.context2.name, self.context2.example)

    def when_something_gets_sent_to_team_city(self):
        self.reporter.assertion_started('aLovelyAssertion')

    @assertion
    def it_should_report_the_name_of_the_current_context(self):
        assert self.parse_line(0)[1]['name'] == 'the second context -> a lovely assertion'


class WhenASecondContextRunsAfterAnError(TeamCitySharedContext):
    def establish_that_a_context_has_run_and_errored(self):
        context1 = tools.create_context('the_first_context')

        self.reporter.context_started(context1.name, context1.example)
        self.reporter.context_errored(context1.name, context1.example, Exception())

        self.context2 = tools.create_context('the_second_context')

        self.reporter.context_started(self.context2.name, self.context2.example)

    def when_something_gets_sent_to_team_city(self):
        self.reporter.assertion_started('aLovelyAssertion')

    @assertion
    def it_should_report_the_name_of_the_current_context(self):
        assert self.parse_line(-1)[1]['name'] == 'the second context -> a lovely assertion'


class WhenEscapingForTeamCity:
    @classmethod
    def examples(self):
        yield "'", "|'"
        yield '\n', "|n"
        yield '\r', "|r"
        yield '|', "||"
        yield '[', '|['
        yield ']', '|]'
        yield '\u0041', 'A'  # should not escape normal ascii
        yield '\u007e', '~'
        yield '\u00df', '|0x00df'  # ß
        yield '\u00e7', '|0x00e7'  # ç

    def context(self, example):
        self.input, self.expected = example

    def because_we_escape_the_char(self):
        self.result = teamcity.escape(self.input)

    def it_should_escape_the_chars_correctly(self):
        assert self.result == self.expected


class WhenParsingATeamCityMessage:
    # tests for the test helper method
    @classmethod
    def examples(self):
        yield "##teamcity[hello]", ('hello', {})
        yield "##teamcity[hello2 ]", ('hello2', {})
        yield "##teamcity[msgName one='value one' two='value two']", ('msgName', {'one':'value one', 'two':'value two'})
        yield "##teamcity[escaped1 name='|'']", ('escaped1', {'name': "|'"})
        yield "##teamcity[escaped2 name='|]']", ('escaped2', {'name': "|]"})

    def context(self, example):
        self.msg, (self.expected_name, self.expected_values) = example

    def because_we_parse_a_message(self):
        self.name, self.values = teamcity_parse(self.msg)

    def it_should_return_the_correct_name(self):
        assert self.name == self.expected_name

    def it_should_return_the_correct_values(self):
        assert self.values == self.expected_values


def teamcity_parse(string):
    outer_match = re.match(r"##teamcity\[(\S+)( .*)?(?<!\|)\]", string)

    assignments_string = outer_match.group(2)
    if assignments_string is not None and assignments_string.strip():
        assignment_matches = re.findall(r"(\w+)='(.*?)(?<!\|)'", assignments_string)
        assignments = dict(assignment_matches)
    else:
        assignments = {}

    return (outer_match.group(1), assignments)
