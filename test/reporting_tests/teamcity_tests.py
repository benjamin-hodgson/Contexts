import sys
from io import StringIO
import re
import sure
from contexts.reporting import teamcity, shared
from .. import tools


class TeamCitySharedContext:
    def shared_context(self):
        self.stringio = StringIO()
        self.notifier = shared.ReporterNotifier(teamcity.TeamCityReporter(self.stringio))
        self.outputs = []

    def get_output(self, n):
        full_output_n = self.outputs[n].strip()
        list_n = full_output_n.split('\n')
        if n != 0:
            full_output_n_minus_1 = self.outputs[n-1].strip()
            list_n_minus_1 = full_output_n_minus_1.split('\n')
            list_n = list_n[len(list_n_minus_1):]
        return [teamcity_parse(s) for s in list_n]


class WhenATestRunPassesInTeamCity(TeamCitySharedContext):
    def establish_that_we_are_spying_on_stdout_and_stderr(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        self.ctx1 = tools.create_context("FakeContext")
        self.ctx2 = tools.create_context("FakeContext2", ["abc", 123, None])
        self.assertion1 = tools.create_assertion("FakeAssertion1")
        self.assertion2 = tools.create_assertion("FakeAssertion2")
        self.assertion3 = tools.create_assertion("FakeAssertion3")

    def because_we_run_some_assertions(self):
        with self.notifier.run_suite(tools.create_suite()):
            self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.ctx1):
                print("to stdout")
                print("to stderr", file=sys.stderr)
                with self.notifier.run_assertion(self.assertion1):
                    self.outputs.append(self.stringio.getvalue())
                self.outputs.append(self.stringio.getvalue())
                with self.notifier.run_assertion(self.assertion2):
                    self.outputs.append(self.stringio.getvalue())
                    print("to stdout again")
                self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.ctx2):
                with self.notifier.run_assertion(self.assertion3):
                    pass
            self.outputs.append(self.stringio.getvalue())

        self.outputs.append(self.stringio.getvalue())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_it_started(self):
        self.get_output(0)[0].should.equal(("testSuiteStarted", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_start(self):
        self.get_output(0).should.have.length_of(1)

    def it_should_tell_team_city_the_first_assertion_started(self):
        self.get_output(1)[0].should.equal(("testStarted", {'name':'Fake context -> Fake assertion 1'}))
    def it_should_not_report_anything_else_at_first_assertion_start(self):
        self.get_output(1).should.have.length_of(1)
    def it_should_tell_team_city_what_went_to_stdout_the_first_time(self):
        self.get_output(2)[0].should.equal(("testStdOut", {'name':'Fake context -> Fake assertion 1', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr_the_first_time(self):
        self.get_output(2)[1].should.equal(("testStdErr", {'name':'Fake context -> Fake assertion 1', 'out':'to stderr|n'}))
    def it_should_tell_team_city_the_first_assertion_passed(self):
        self.get_output(2)[2].should.equal(("testFinished", {'name':'Fake context -> Fake assertion 1'}))
    def it_should_not_report_anything_else_at_first_assertion_end(self):
        self.get_output(2).should.have.length_of(3)

    def it_should_tell_team_city_the_second_assertion_started(self):
        self.get_output(3)[0].should.equal(("testStarted", {'name':'Fake context -> Fake assertion 2'}))
    def it_should_not_report_anything_else_at_second_assertion_start(self):
        self.get_output(3).should.have.length_of(1)
    def it_should_tell_team_city_what_went_to_stdout_the_second_time(self):
        self.get_output(4)[0].should.equal(("testStdOut", {'name':'Fake context -> Fake assertion 2', 'out':'to stdout|nto stdout again|n'}))
    def it_should_tell_team_city_what_went_to_stderr_the_second_time(self):
        self.get_output(4)[1].should.equal(("testStdErr", {'name':'Fake context -> Fake assertion 2', 'out':'to stderr|n'}))
    def it_should_tell_team_city_the_second_assertion_passed(self):
        self.get_output(4)[2].should.equal(("testFinished", {'name':'Fake context -> Fake assertion 2'}))
    def it_should_not_report_anything_else_at_second_assertion_end(self):
        self.get_output(4).should.have.length_of(3)

    def it_should_report_the_exmpl(self):
        # also asserting that nothing about stdout comes out here
        self.get_output(5)[0].should.equal(("testStarted", {'name':"Fake context 2 -> |[|'abc|', 123, None|] -> Fake assertion 3"}))
        self.get_output(5)[1].should.equal(("testFinished", {'name':"Fake context 2 -> |[|'abc|', 123, None|] -> Fake assertion 3"}))
    def it_should_not_report_anything_following_the_second_ctx(self):
        self.get_output(5).should.have.length_of(2)

    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(6)[0].should.equal(("testSuiteFinished", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_suite_end(self):
        self.get_output(6).should.have.length_of(1)

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


class WhenAnAssertionFailsInTeamCity(TeamCitySharedContext):
    def establish_that_we_are_spying_on_stdout_and_stderr(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

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
        self.assertion = tools.create_assertion("FakeAssertion3")
        self.context = tools.create_context("FakeContext")

    def because_we_run_an_assertion(self):
        with self.notifier.run_suite(tools.create_suite()):
            self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.context):
                print("to stdout")
                print("to stderr", file=sys.stderr)
                with self.notifier.run_assertion(self.assertion):
                    self.outputs.append(self.stringio.getvalue())
                    raise self.exception
                self.outputs.append(self.stringio.getvalue())

        self.outputs.append(self.stringio.getvalue())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_it_started(self):
        self.get_output(0)[0].should.equal(("testSuiteStarted", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_start(self):
        self.get_output(0).should.have.length_of(1)

    def it_should_tell_team_city_the_assertion_started(self):
        self.get_output(1)[0].should.equal(("testStarted", {'name':'Fake context -> Fake assertion 3'}))
    def it_should_not_report_anything_else_at_assertion_start(self):
        self.get_output(1).should.have.length_of(1)
    def it_should_tell_team_city_what_went_to_stdout(self):
        self.get_output(2)[0].should.equal(("testStdOut", {'name':'Fake context -> Fake assertion 3', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr(self):
        self.get_output(2)[1].should.equal(("testStdErr", {'name':'Fake context -> Fake assertion 3', 'out':'to stderr|n'}))
    def it_should_tell_team_city_the_assertion_failed(self):
        self.get_output(2)[2].should.equal(("testFailed", {'name':'Fake context -> Fake assertion 3', 'message':'test.tools.FakeAssertionError: Gotcha', 'details':self.formatted_tb}))
        self.get_output(2)[3].should.equal(("testFinished", {'name':'Fake context -> Fake assertion 3'}))
    def it_should_not_report_anything_else_at_assertion_end(self):
        self.get_output(2).should.have.length_of(4)

    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(3)[0].should.equal(("testSuiteFinished", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_suite_end(self):
        self.get_output(3).should.have.length_of(1)

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


class WhenAnAssertionErrorsInTeamCity(TeamCitySharedContext):
    def establish_that_we_are_spying_on_stdout_and_stderr(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        tb = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
               ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "you fail")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file_3.py", line 1, in made_up_function_3|n'
'    frame3|n'
'  File "made_up_file_4.py", line 2, in made_up_function_4|n'
'    frame4|n'
'test.tools.FakeException: you fail')
        self.context = tools.create_context("FakeContext")
        self.assertion = tools.create_assertion("FakeAssertion4")

    def because_we_run_an_assertion(self):
        with self.notifier.run_suite(tools.create_suite()):
            self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.context):
                print("to stdout")
                print("to stderr", file=sys.stderr)
                with self.notifier.run_assertion(self.assertion):
                    self.outputs.append(self.stringio.getvalue())
                    raise self.exception
                self.outputs.append(self.stringio.getvalue())

        self.outputs.append(self.stringio.getvalue())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_it_started(self):
        self.get_output(0)[0].should.equal(("testSuiteStarted", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_start(self):
        self.get_output(0).should.have.length_of(1)

    def it_should_tell_team_city_the_assertion_started(self):
        self.get_output(1)[0].should.equal(("testStarted", {'name':'Fake context -> Fake assertion 4'}))
    def it_should_not_report_anything_else_at_assertion_start(self):
        self.get_output(1).should.have.length_of(1)
    def it_should_tell_team_city_what_went_to_stdout(self):
        self.get_output(2)[0].should.equal(("testStdOut", {'name':'Fake context -> Fake assertion 4', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr(self):
        self.get_output(2)[1].should.equal(("testStdErr", {'name':'Fake context -> Fake assertion 4', 'out':'to stderr|n'}))
    def it_should_output_a_stack_trace_for_the_assertion(self):
        self.get_output(2)[2].should.equal(("testFailed", {'name':'Fake context -> Fake assertion 4', 'message':'test.tools.FakeException: you fail', 'details':self.formatted_tb}))
        self.get_output(2)[3].should.equal(("testFinished", {'name':'Fake context -> Fake assertion 4'}))
    def it_should_not_report_anything_else_at_assertion_end(self):
        self.get_output(2).should.have.length_of(4)

    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(3)[0].should.equal(("testSuiteFinished", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_suite_end(self):
        self.get_output(3).should.have.length_of(1)

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


class WhenAContextErrorsInTeamCity(TeamCitySharedContext):
    def establish_that_we_are_spying_on_stdout_and_stderr(self):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.fake_stdout, self.fake_stderr = StringIO(), StringIO()

        tb = [('made_up_file_5.py', 1, 'made_up_function_5', 'frame5'),
               ('made_up_file_6.py', 2, 'made_up_function_6', 'frame6')]
        self.exception = tools.build_fake_exception(tb, "oh dear")
        self.formatted_tb = (
'Traceback (most recent call last):|n'
'  File "made_up_file_5.py", line 1, in made_up_function_5|n'
'    frame5|n'
'  File "made_up_file_6.py", line 2, in made_up_function_6|n'
'    frame6|n'
'test.tools.FakeException: oh dear')

        self.ctx = tools.create_context("FakeContext")

    def because_we_run_an_assertion(self):
        with self.notifier.run_suite(tools.create_suite()):
            self.outputs.append(self.stringio.getvalue())

            with self.notifier.run_context(self.ctx):
                print("to stdout")
                print("to stderr", file=sys.stderr)
                raise self.exception
            self.outputs.append(self.stringio.getvalue())

        self.outputs.append(self.stringio.getvalue())

    def it_should_not_print_anything_to_the_real_stdout(self):
        self.fake_stdout.getvalue().should.be.empty
    def it_should_not_print_anything_to_the_real_stderr(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_tell_team_city_it_started(self):
        self.get_output(0)[0].should.equal(("testSuiteStarted", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_start(self):
        self.get_output(0).should.have.length_of(1)

    def it_should_tell_team_city_another_test_started(self):
        self.get_output(1)[0].should.equal(("testStarted", {'name':'Fake context'}))
    def it_should_tell_team_city_what_went_to_stdout(self):
        self.get_output(1)[1].should.equal(("testStdOut", {'name':'Fake context', 'out':'to stdout|n'}))
    def it_should_tell_team_city_what_went_to_stderr(self):
        self.get_output(1)[2].should.equal(("testStdErr", {'name':'Fake context', 'out':'to stderr|n'}))
    def it_should_tell_team_city_the_test_failed(self):
        self.get_output(1)[3].should.equal(("testFailed", {'name':'Fake context', 'message':'test.tools.FakeException: oh dear', 'details':self.formatted_tb}))
        self.get_output(1)[4].should.equal(("testFinished", {'name':'Fake context'}))
    def it_should_not_report_anything_else_following_the_ctx_error(self):
        self.get_output(1).should.have.length_of(5)

    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(2)[0].should.equal(("testSuiteFinished", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_suite_end(self):
        self.get_output(2).should.have.length_of(1)

    def cleanup_stdout_and_stderr(self):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr


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
'test.tools.FakeException: another exception')

    def because_we_run_some_assertions(self):
        # unexpected error happens when (for example) a syntax error occurs
        # in the user's test code. Very unlikely that anything will have been printed
        # at this stage.
        with self.notifier.run_suite(tools.create_suite()):
            self.outputs.append(self.stringio.getvalue())

            raise self.exception

        self.outputs.append(self.stringio.getvalue())

    def it_should_tell_team_city_it_started(self):
        self.get_output(0)[0].should.equal(("testSuiteStarted", {'name':'contexts'}))
    def it_should_not_report_anything_else_at_start(self):
        self.get_output(0).should.have.length_of(1)

    def it_should_tell_team_city_a_test_started_and_failed_for_the_unexpected_error(self):
        self.get_output(1)[0].should.equal(("testStarted", {'name':'Test error'}))
        self.get_output(1)[1].should.equal(("testFailed", {'name':'Test error', 'message':'test.tools.FakeException: another exception', 'details':self.formatted_tb}))
        self.get_output(1)[2].should.equal(("testFinished", {'name':'Test error'}))
    def it_should_tell_team_city_the_suite_ended(self):
        self.get_output(1)[3].should.equal(("testSuiteFinished", {'name':'contexts'}))
    def it_should_not_report_anything_else_following_unexpected_error(self):
        self.get_output(1).should.have.length_of(4)


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
