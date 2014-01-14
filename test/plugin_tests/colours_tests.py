from io import StringIO
import contexts
from contexts import plugins
from . import tools


class ColouredReporterSharedContext:
    def shared_context(self):
        self.stringio = StringIO()
        self.reporter = plugins.cli.ColouringDecorator(plugins.cli.VerboseReporter)(self.stringio)


class WhenColouringOutputAndAnAssertionPasses(ColouredReporterSharedContext):
    def because_the_assertion_passes(self):
        self.reporter.assertion_passed("assertion")

    def it_should_output_the_name_in_green(self):
        assert self.stringio.getvalue() == '\x1b[32m  PASS: assertion\n\x1b[39m'


class WhenColouringOutputAndAnAssertionFails(ColouredReporterSharedContext):
    def establish_the_exception(self):
        tb = [('made_up_file_10.py', 1, 'made_up_function_1', 'frame1'),
               ('made_up_file_11.py', 2, 'made_up_function_2', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "you fail")

    def because_the_assertion_fails(self):
        self.reporter.assertion_failed("assertion", self.exception)

    def it_should_output_a_red_stack_trace_for_the_failed_assertion(self):
        assert self.stringio.getvalue() == (
"""\x1b[31m  FAIL: assertion
    Traceback (most recent call last):
      File "made_up_file_10.py", line 1, in made_up_function_1
        frame1
      File "made_up_file_11.py", line 2, in made_up_function_2
        frame2
    plugin_tests.tools.FakeAssertionError: you fail
\x1b[39m""")


class WhenColouringOutputAndAnAssertionErrors(ColouredReporterSharedContext):
    def establish_the_exception(self):
        tb = [('made_up_file_12.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_13.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "no")

    def because_the_assertion_errors(self):
        self.reporter.assertion_errored("assertion", self.exception)

    def it_should_output_a_red_stack_trace(self):
        assert self.stringio.getvalue() == (
"""\x1b[31m  ERROR: assertion
    Traceback (most recent call last):
      File "made_up_file_12.py", line 3, in made_up_function_3
        frame3
      File "made_up_file_13.py", line 4, in made_up_function_4
        frame4
    plugin_tests.tools.FakeException: no
\x1b[39m""")


class WhenColouringOutputAndAContextErrors(ColouredReporterSharedContext):
    def establish_the_exception(self):
        self.context = tools.create_context()
        tb = [('made_up_file_14.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_15.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")

    @contexts.action
    def because_the_context_errors(self):
        self.reporter.context_errored(self.context.name, self.context.example, self.exception)

    def it_should_output_a_red_stack_trace(self):
        assert self.stringio.getvalue() == (
"""\x1b[31m  Traceback (most recent call last):
    File "made_up_file_14.py", line 3, in made_up_function_3
      frame3
    File "made_up_file_15.py", line 4, in made_up_function_4
      frame4
  plugin_tests.tools.FakeException: out
\x1b[39m""")


class WhenColouringOutputAndAnUnexpectedErrorOccurs(ColouredReporterSharedContext):
    def establish_the_exception(self):
        tb = [('made_up_file_16.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_17.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")

    def because_an_unexpected_error_occurs(self):
        self.reporter.unexpected_error(self.exception)

    def it_should_output_a_red_stack_trace(self):
        assert self.stringio.getvalue() == (
"""\x1b[31mTraceback (most recent call last):
  File "made_up_file_16.py", line 3, in made_up_function_3
    frame3
  File "made_up_file_17.py", line 4, in made_up_function_4
    frame4
plugin_tests.tools.FakeException: out
\x1b[39m""")
