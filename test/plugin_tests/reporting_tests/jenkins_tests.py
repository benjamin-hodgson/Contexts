import argparse
import collections
import os
import tempfile
import xml.etree.ElementTree as ET

from contexts.plugins.reporting import jenkins
from .. import tools


Args = collections.namedtuple("Args", ["jenkins_out"])

# Initialisation tests


class When_the_plugin_is_initialised:

    def given_an_jenkins_reporter(self):
        self.jenkins = jenkins.JenkinsReporter()

    def because_we_initialise_with_an_jenkins_output_path(self):
        self.initialised = self.jenkins.initialise(Args("foo"), None)

    def it_should_return_true(self):
        assert(self.initialised is True)


class When_the_plugin_is_initialised_without_an_output_file:

    def given_an_jenkins_reporter(self):
        self.jenkins = jenkins.JenkinsReporter()

    def because_we_initialise_with_an_jenkins_output_path(self):
        self.initialised = self.jenkins.initialise(Args(None), None)

    def it_should_return_false(self):
        assert(self.initialised is False)


class When_the_plugin_sets_up_argparser:

    def given_a_parser(self):
        self.parser = argparse.ArgumentParser()
        self.jenkins = jenkins.JenkinsReporter()
        self.jenkins.setup_parser(self.parser)

    def because_we_initialise_from_args(self):
        args = self.parser.parse_args('--jenkins-out=foo'.split())
        self.initialised = self.jenkins.initialise(args, None)

    def it_should_initialise_with_the_args(self):
        assert(self.initialised is True)

    def it_should_have_the_correct_path(self):
        assert(self.jenkins.path == 'foo')


# Context tests

class JenkinsOutputContext:

    def given_an_jenkins_reporter(self):
        self.jenkins = jenkins.JenkinsReporter()
        self.tempdir = tempfile.TemporaryDirectory()
        self.filename = os.path.join(self.tempdir.name, "output.xml")
        self.jenkins.path = self.filename

    def cleanup_the_tempdir(self):
        self.tempdir.cleanup()

    @property
    def test_suites(self):
        tree = ET.parse(self.filename).getroot()
        print(ET.tostring(tree))
        return tree


class When_a_context_begins(JenkinsOutputContext):

    def because_a_ctx_starts(self):
        ctx = tools.create_context('When_a_context_starts')
        self.jenkins.context_started(ctx.cls)
        self.jenkins.test_run_ended()

    def it_should_include_the_suite_in_the_output(self):
        assert(self.suite.get('name') == 'When a context starts')

    def it_should_have_run_no_tests(self):
        assert(self.suite.get("tests") == "0")

    def it_should_not_have_failed(self):
        assert(self.suite.get("failures") == "0")

    def it_should_not_have_raised_any_errors(self):
        assert(self.suite.get("errors") == "0")

    def the_suites_element_should_report_zero_tests(self):
        assert(self.test_suites.get("tests") == "0")

    def the_suites_element_should_report_zero_errors(self):
        assert(self.test_suites.get("errors") == "0")

    def the_suites_element_should_report_zero_failures(self):
        assert(self.test_suites.get("failures") == "0")

    @property
    def suite(self):
        return self.test_suites.find('testsuite')


class When_an_assertion_passes(JenkinsOutputContext):

    def because_a_test_succeeds(self):
        ctx = tools.create_context('When_a_test_succeeds')
        assertion = lambda: None
        assertion.__name__ = 'it_should_be_counted_as_a_success'

        self.jenkins.context_started(ctx.cls)
        self.jenkins.assertion_started(assertion)
        self.jenkins.assertion_passed(assertion)
        self.jenkins.test_run_ended()

    def it_should_have_run_one_test(self):
        assert(self.suite.get("tests") == "1")

    def it_should_output_the_test(self):
        assert(self.test.get("name") == "it should be counted as a success")

    def it_should_not_have_an_error(self):
        assert(self.test.find("error") is None)

    def it_should_not_have_a_failure(self):
        assert(self.test.find("failure") is None)

    def it_should_not_have_been_skipped(self):
        assert(self.test.find("skipped") is None)

    def the_suite_should_not_have_failed(self):
        assert(self.suite.get("failures") == "0")

    def the_suite_should_not_have_raised_any_errors(self):
        assert(self.suite.get("errors") == "0")

    def the_suites_element_should_report_one_test(self):
        assert(self.test_suites.get("tests") == "1")

    def the_suites_element_should_report_zero_errors(self):
        assert(self.test_suites.get("errors") == "0")

    def the_suites_element_should_report_zero_failures(self):
        assert(self.test_suites.get("failures") == "0")

    @property
    def suite(self):
        return self.test_suites.find('testsuite')

    @property
    def test(self):
        return self.suite.find('testcase')


class When_an_assertion_fails(JenkinsOutputContext):

    def because_a_test_fails(self):
        ctx = tools.create_context('When_a_test_fails')
        assertion = lambda: None
        assertion.__name__ = 'it_should_be_counted_as_a_failure'
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
        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]

        self.jenkins.context_started(ctx.cls)
        self.jenkins.assertion_started(assertion)
        self.jenkins.assertion_failed(assertion, self.exception)
        self.jenkins.test_run_ended()

    def it_should_have_run_one_test(self):
        assert(self.suite.get("tests") == "1")

    def it_should_output_the_test(self):
        assert(self.test.get("name") == "it should be counted as a failure")

    def it_should_not_have_an_error(self):
        assert(self.test.find("error") is None)

    def it_should_have_a_failure(self):
        assert(self.test.find("failure") is not None)

    def it_should_have_a_short_message(self):
        assert(self.test.find("failure").get("message") == "Gotcha")

    def it_should_not_have_been_skipped(self):
        assert(self.test.find("skipped") is None)

    def the_suite_should_have_failed(self):
        assert(self.suite.get("failures") == "1")

    def the_suite_should_not_have_raised_any_errors(self):
        assert(self.suite.get("errors") == "0")

    def the_suites_element_should_report_one_test(self):
        assert(self.test_suites.get("tests") == "1")

    def the_suites_element_should_report_zero_errors(self):
        assert(self.test_suites.get("errors") == "0")

    def the_suites_element_should_report_one_failure(self):
        assert(self.test_suites.get("failures") == "1")

    @property
    def suite(self):
        return self.test_suites.find('testsuite')

    @property
    def test(self):
        return self.suite.find('testcase')


class When_an_assertion_errors(JenkinsOutputContext):

    def because_a_test_errors(self):
        ctx = tools.create_context('When_a_test_fails')
        assertion = lambda: None
        assertion.__name__ = 'it_should_be_counted_as_an_error'
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
        tb = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
              ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]

        self.jenkins.context_started(ctx.cls)
        self.jenkins.assertion_started(assertion)
        self.jenkins.assertion_errored(assertion, self.exception)
        self.jenkins.test_run_ended()

    def it_should_have_run_one_test(self):
        assert(self.suite.get("tests") == "1")

    def it_should_output_the_test(self):
        assert(self.test.get("name") == "it should be counted as an error")

    def it_should_not_have_a_failure(self):
        assert(self.test.find("failure") is None)

    def it_should_have_an_error(self):
        assert(self.test.find("error") is not None)

    def it_should_have_a_short_message(self):
        assert(self.test.find("error").get("message") == "Gotcha")

    def it_should_not_have_been_skipped(self):
        assert(self.test.find("skipped") is None)

    def the_suite_should_not_have_failed(self):
        assert(self.suite.get("failures") == "0")

    def the_suite_should_have_raised_any_errors(self):
        assert(self.suite.get("errors") == "1")

    def the_suites_element_should_report_one_test(self):
        assert(self.test_suites.get("tests") == "1")

    def the_suites_element_should_report_one_error1(self):
        assert(self.test_suites.get("errors") == "1")

    def the_suites_element_should_report_no_failures(self):
        assert(self.test_suites.get("failures") == "0")

    @property
    def suite(self):
        return self.test_suites.find('testsuite')

    @property
    def test(self):
        return self.suite.find('testcase')
