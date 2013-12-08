import sys
from io import StringIO
import re
import sure
import contexts
from contexts.reporting import teamcity
from .. import tools


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
    def because_the_suite_starts(self):
        self.reporter.suite_started(tools.create_suite('test_suite'))
    def it_should_tell_team_city_the_suite_started(self):
        teamcity_parse(self.stringio.getvalue()).should.equal(("testSuiteStarted", {'name':'test suite'}))


class WhenASuiteEndsInTeamCity(TeamCitySharedContext):
    def because_the_suite_ends(self):
        self.reporter.suite_ended(tools.create_suite('mah_suite'))
    def it_should_tell_team_city_the_suite_ended(self):
        teamcity_parse(self.stringio.getvalue()).should.equal(("testSuiteFinished", {'name':'mah suite'}))


###########################################################
# assertion_started tests
###########################################################

class WhenAnAssertionStartsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('MyNiceContext')
        self.assertion = tools.create_assertion('aLovelyAssertion')
        self.reporter.context_started(context)

    def because_the_assertion_starts(self):
        self.reporter.assertion_started(self.assertion)

    def it_should_tell_team_city_it_started(self):
        self.parse_line(0).should.equal(("testStarted", {'name':'My nice context -> a lovely assertion'}))


class WhenAnAssertionInAContextWithExamplesStartsInTeamCity(TeamCitySharedContext):
    @contexts.setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.assertion = tools.create_assertion('aLovelyAssertion')
        self.reporter.context_started(context)

    def because_the_assertion_starts(self):
        self.reporter.assertion_started(self.assertion)

    @contexts.assertion
    def it_should_report_the_example(self):
        self.parse_line(0)[1]['name'].should.equal('Context with examples -> 12.3 -> a lovely assertion')


###########################################################
# assertion_passed tests
###########################################################

class WhenAnAssertionPassesInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('MyNiceContext')
        self.assertion = tools.create_assertion('aLovelyAssertion')
        self.reporter.context_started(context)
    def because_the_assertion_ends(self):
        self.reporter.assertion_passed(self.assertion)
    def it_should_tell_team_city_it_passed(self):
        self.parse_line(0).should.equal(("testFinished", {'name':'My nice context -> a lovely assertion'}))


class WhenAnAssertionInAContextWithExamplesPassesInTeamCity(TeamCitySharedContext):
    @contexts.setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.assertion = tools.create_assertion('aLovelyAssertion')
        self.reporter.context_started(context)
    def because_the_assertion_passes(self):
        self.reporter.assertion_passed(self.assertion)
    @contexts.assertion
    def it_should_report_the_example(self):
        self.parse_line(0)[1]['name'].should.equal('Context with examples -> 12.3 -> a lovely assertion')


class WhenSomethingGetsPrintedDuringAPassingAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        context = tools.create_context('Context')
        self.assertion = tools.create_assertion('assertion')

        self.reporter.context_started(context)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_the_assertion_passes(self):
        self.reporter.assertion_passed(self.assertion)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_stderr(self):
        self.fake_stderr.getvalue().should.be.empty

    def it_should_report_what_went_to_stdout(self):
        self.parse_line(0).should.equal(("testStdOut", {'name':'Context -> assertion', 'out':'to stdout|n'}))
    def it_should_report_what_went_to_stderr(self):
        self.parse_line(1).should.equal(("testStdErr", {'name':'Context -> assertion', 'out':'to stderr|n'}))

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# assertion_failed tests
###########################################################

class WhenAnAssertionFailsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('FakeContext')
        self.assertion = tools.create_assertion('Fake_assertion')

        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "Gotcha")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'test.tools.FakeAssertionError: Gotcha')

        self.reporter.context_started(context)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed(self.assertion, self.exception)

    def it_should_tell_team_city_it_failed(self):
        self.parse_line(0).should.equal((
            "testFailed",
            {
                'name':'Fake context -> Fake assertion',
                'message':'test.tools.FakeAssertionError: Gotcha',
                'details':self.formatted_tb
            }))
    def it_should_tell_team_city_it_finished(self):
        self.parse_line(1).should.equal(("testFinished", {'name':'Fake context -> Fake assertion'}))


class WhenAnAssertionInAContextWithExamplesFailsInTeamCity(TeamCitySharedContext):
    @contexts.setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.assertion = tools.create_assertion('aLovelyAssertion')

        self.reporter.context_started(context)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed(self.assertion, Exception())

    @contexts.assertion
    def it_should_report_the_example(self):
        self.parse_line(0)[1]['name'].should.equal('Context with examples -> 12.3 -> a lovely assertion')


class WhenSomethingGetsPrintedDuringAFailingAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        context = tools.create_context('Context')
        self.assertion = tools.create_assertion('assertion')

        self.reporter.context_started(context)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed(self.assertion, Exception())

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_stderr(self):
        self.fake_stderr.getvalue().should.be.empty

    def it_should_report_what_went_to_stdout(self):
        self.parse_line(0).should.equal(("testStdOut", {'name':'Context -> assertion', 'out':'to stdout|n'}))
    def it_should_report_what_went_to_stderr(self):
        self.parse_line(1).should.equal(("testStdErr", {'name':'Context -> assertion', 'out':'to stderr|n'}))

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# assertion_errored tests
###########################################################

class WhenAnAssertionErrorsInTeamCity(TeamCitySharedContext):
    def establish_that_a_context_is_running(self):
        context = tools.create_context('FakeContext')
        self.assertion = tools.create_assertion('Fake_assertion')

        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "Gotcha")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file.py", line 3, in made_up_function|n'
'    frame1|n'
'  File "another_made_up_file.py", line 2, in another_made_up_function|n'
'    frame2|n'
'test.tools.FakeAssertionError: Gotcha')

        self.reporter.context_started(context)

    def because_the_assertion_errors(self):
        self.reporter.assertion_errored(self.assertion, self.exception)

    def it_should_tell_team_city_it_failed(self):
        self.parse_line(0).should.equal((
            "testFailed",
            {
                'name':'Fake context -> Fake assertion',
                'message':'test.tools.FakeAssertionError: Gotcha',
                'details':self.formatted_tb
            }))
    def it_should_tell_team_city_it_finished(self):
        self.parse_line(1).should.equal(("testFinished", {'name':'Fake context -> Fake assertion'}))


class WhenAnAssertionInAContextWithExamplesErrorsInTeamCity(TeamCitySharedContext):
    @contexts.setup
    def establish_that_a_context_with_an_example_is_running(self):
        context = tools.create_context('ContextWithExamples', 12.3)
        self.assertion = tools.create_assertion('aLovelyAssertion')

        self.reporter.context_started(context)

    def because_the_assertion_errors(self):
        self.reporter.assertion_errored(self.assertion, Exception())

    @contexts.assertion
    def it_should_report_the_example(self):
        self.parse_line(0)[1]['name'].should.equal('Context with examples -> 12.3 -> a lovely assertion')


class WhenSomethingGetsPrintedDuringAnErroringAssertionInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        self.context = tools.create_context("FakeContext")
        self.assertion = tools.create_assertion("FakeAssertion4")

        self.reporter.context_started(self.context)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_we_run_an_assertion(self):
        self.reporter.assertion_errored(self.assertion, Exception())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_what_went_to_stdout(self):
        self.parse_line(0).should.equal(("testStdOut", {'name':'Fake context -> Fake assertion 4', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr(self):
        self.parse_line(1).should.equal(("testStdErr", {'name':'Fake context -> Fake assertion 4', 'out':'to stderr|n'}))

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
'test.tools.FakeException: Gotcha')

        self.reporter.context_started(self.context)

    def because_we_run_an_assertion(self):
        self.reporter.context_errored(self.context, self.exception)

    def it_should_tell_team_city_a_test_started(self):
        self.parse_line(0).should.equal(("testStarted", {'name':'Fake context'}))
    def it_should_tell_team_city_the_test_failed(self):
        self.parse_line(1).should.equal((
            "testFailed",
            {
                'name':'Fake context',
                'message':'test.tools.FakeException: Gotcha',
                'details':self.formatted_tb
            }))
    def it_should_tell_team_city_the_test_finished(self):
        self.parse_line(2).should.equal(("testFinished", {'name':'Fake context'}))


class WhenAContextWithExamplesErrorsInTeamCity(TeamCitySharedContext):
    @contexts.setup
    def establish_that_a_context_with_an_example_is_running(self):
        self.context = tools.create_context('ContextWithExamples', 12.3)
        self.reporter.context_started(self.context)

    @contexts.action
    def because_the_context_errors(self):
        self.reporter.context_errored(self.context, Exception())

    @contexts.assertion
    def it_should_report_the_example(self):
        self.parse_line(0)[1]['name'].should.equal('Context with examples -> 12.3')


class WhenSomethingGetsPrintedDuringAnErroringContextInTeamCity(TeamCitySharedContext):
    def establish_that_something_has_been_printed(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        self.context = tools.create_context("FakeContext")

        self.reporter.context_started(self.context)
        print("to stdout")
        print("to stderr", file=sys.stderr)

    def because_we_run_an_assertion(self):
        self.reporter.context_errored(self.context, Exception())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_what_went_to_stdout(self):
        self.parse_line(1).should.equal(("testStdOut", {'name':'Fake context', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr(self):
        self.parse_line(2).should.equal(("testStdErr", {'name':'Fake context', 'out':'to stderr|n'}))

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


###########################################################
# unexpected_error tests
###########################################################

class WhenAnUnexpectedErrorOccursInTeamCity(TeamCitySharedContext):
    def establish_the_exception(self):
        tb = [('made_up_file_7.py', 1, 'made_up_function_7', 'frame7'),
               ('made_up_file_8.py', 2, 'made_up_function_8', 'frame8')]
        self.suite = tools.create_suite()
        self.exception = tools.build_fake_exception(tb, "another exception")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file_7.py", line 1, in made_up_function_7|n'
'    frame7|n'
'  File "made_up_file_8.py", line 2, in made_up_function_8|n'
'    frame8|n'
'test.tools.FakeException: another exception')

    def because_an_unexpected_error_occurs(self):
        self.reporter.unexpected_error(self.exception)

    def it_should_tell_team_city_a_test_started(self):
        self.parse_line(0).should.equal(("testStarted", {'name':'Test error'}))
    def it_should_tell_team_city_the_test_failed(self):
        self.parse_line(1).should.equal((
            "testFailed",
            {
                'name':'Test error',
                'message':'test.tools.FakeException: another exception',
                'details':self.formatted_tb
            }))
    def it_should_tell_team_city_the_test_finished(self):
        self.parse_line(2).should.equal(("testFinished", {'name':'Test error'}))


###########################################################
# tests for sequential calls
###########################################################
# these are really testing context_ended and context_errored,
# but sadly we can only observe it through assertion_started

class WhenASecondContextRuns(TeamCitySharedContext):
    def establish_that_a_context_has_run_and_ended(self):
        context1 = tools.create_context('the_first_context')

        self.reporter.context_started(context1)
        self.reporter.context_ended(context1)

        self.context2 = tools.create_context('the_second_context')
        self.assertion = tools.create_assertion('aLovelyAssertion')

        self.reporter.context_started(self.context2)

    def when_something_gets_sent_to_team_city(self):
        self.reporter.assertion_started(self.assertion)

    @contexts.assertion
    def it_should_report_the_name_of_the_current_context(self):
        self.parse_line(0)[1]['name'].should.equal('the second context -> a lovely assertion')


class WhenASecondContextRunsAfterAnError(TeamCitySharedContext):
    def establish_that_a_context_has_run_and_errored(self):
        context1 = tools.create_context('the_first_context')

        self.reporter.context_started(context1)
        self.reporter.context_errored(context1, Exception())

        self.context2 = tools.create_context('the_second_context')
        self.assertion = tools.create_assertion('aLovelyAssertion')

        self.reporter.context_started(self.context2)

    def when_something_gets_sent_to_team_city(self):
        self.reporter.assertion_started(self.assertion)

    @contexts.assertion
    def it_should_report_the_name_of_the_current_context(self):
        self.parse_line(-1)[1]['name'].should.equal('the second context -> a lovely assertion')


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
        self.result.should.equal(self.expected)


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
        self.name.should.equal(self.expected_name)

    def it_should_return_the_correct_values(self):
        self.values.should.equal(self.expected_values)


def teamcity_parse(string):
    outer_match = re.match(r"##teamcity\[(\S+)( .*)?(?<!\|)\]", string)

    assignments_string = outer_match.group(2)
    if assignments_string is not None and assignments_string.strip():
        assignment_matches = re.findall(r"(\w+)='(.*?)(?<!\|)'", assignments_string)
        assignments = dict(assignment_matches)
    else:
        assignments = {}

    return (outer_match.group(1), assignments)


if __name__ == "__main__":
    import contexts
    contexts.main()
