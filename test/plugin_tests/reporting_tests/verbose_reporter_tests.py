from io import StringIO
from contexts.plugins.reporting import cli
from contexts.plugins.decorators import action
from .. import tools


class VerboseReporterSharedContext:
    def context(self):
        self.stringio = StringIO()
        self.reporter = cli.VerboseReporter(self.stringio)
        self.outputs = []

class WhenPrintingVerboselyAndAContextStarts(VerboseReporterSharedContext):
    def context(self):
        self.ctx = tools.create_context("made.up_context_1")
    @action
    def because_a_context_starts(self):
        self.reporter.context_started(self.ctx.name, self.ctx.example)
    def it_should_print_its_name(self):
        assert self.stringio.getvalue() == "made up context 1\n"

class WhenPrintingVerboselyAndAnAssertionPasses(VerboseReporterSharedContext):
    def because_an_assertion_passes(self):
        self.reporter.assertion_passed("assertion1")
    def it_should_say_the_assertion_passed(self):
        assert self.stringio.getvalue() == '  PASS: assertion 1\n'

class WhenPrintingVerboselyAndAnAssertionFails(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_10.py', 1, 'made_up_function_1', 'frame1'),
              ('made_up_file_11.py', 2, 'made_up_function_2', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "you fail")

    def because_an_assertion_fails(self):
        self.reporter.assertion_failed("assertion2", self.exception)

    def it_should_output_a_stack_trace(self):
        assert self.stringio.getvalue() == (
"""  FAIL: assertion 2
    Traceback (most recent call last):
      File "made_up_file_10.py", line 1, in made_up_function_1
        frame1
      File "made_up_file_11.py", line 2, in made_up_function_2
        frame2
    plugin_tests.tools.FakeAssertionError: you fail
""")

class WhenPrintingVerboselyAndAnAssertionErrors(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_12.py', 3, 'made_up_function_3', 'frame3'),
              ('made_up_file_13.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "no")

    def because_an_assertion_errors(self):
        self.reporter.assertion_errored("assertion3", self.exception)

    def it_should_output_a_stack_trace(self):
        assert self.stringio.getvalue() == (
"""  ERROR: assertion 3
    Traceback (most recent call last):
      File "made_up_file_12.py", line 3, in made_up_function_3
        frame3
      File "made_up_file_13.py", line 4, in made_up_function_4
        frame4
    plugin_tests.tools.FakeException: no
""")

class WhenPrintingVerboselyAndAContextErrors(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_14.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_15.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")
        self.ctx = tools.create_context("made.up_context_2", ["abc", 123])

    @action
    def because_a_context_errors(self):
        self.reporter.context_errored(self.ctx.name, self.ctx.example, self.exception)

    def it_should_output_a_stack_trace(self):
        assert self.stringio.getvalue() == (
"""  Traceback (most recent call last):
    File "made_up_file_14.py", line 3, in made_up_function_3
      frame3
    File "made_up_file_15.py", line 4, in made_up_function_4
      frame4
  plugin_tests.tools.FakeException: out
""")

class WhenPrintingVerboselyAndAnUnexpectedErrorOccurs(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_16.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_17.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")
    def because_an_unexpected_error_occurs(self):
        self.reporter.unexpected_error(self.exception)
    def it_should_output_a_stack_trace(self):
        assert self.stringio.getvalue() == (
"""Traceback (most recent call last):
  File "made_up_file_16.py", line 3, in made_up_function_3
    frame3
  File "made_up_file_17.py", line 4, in made_up_function_4
    frame4
plugin_tests.tools.FakeException: out
""")
