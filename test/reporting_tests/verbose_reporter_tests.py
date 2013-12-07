from io import StringIO
import sure
import contexts
from contexts import reporting
from .. import tools


class VerboseReporterSharedContext:
    def context(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.VerboseReporter(self.stringio)
        self.outputs = []

class WhenPrintingVerboselyAndASuiteEnds(VerboseReporterSharedContext):
    def because_a_suite_ends(self):
        self.reporter.suite_ended(tools.create_suite())
    def it_should_output_a_summary(self):
        self.stringio.getvalue().should.equal("""
----------------------------------------------------------------------
PASSED!
0 contexts, 0 assertions
""")
# TODO: tests that make assertions about the counts

class WhenPrintingVerboselyAndAContextStarts(VerboseReporterSharedContext):
    @contexts.action
    def because_a_context_starts(self):
        self.reporter.context_started(tools.create_context("made.up_context_1"))
    def it_should_print_its_name(self):
        self.stringio.getvalue().should.equal("made up context 1\n")

class WhenPrintingVerboselyAndAnAssertionPasses(VerboseReporterSharedContext):
    def because_an_assertion_passes(self):
        self.reporter.assertion_passed(tools.create_assertion("assertion1"))
    def it_should_say_the_assertion_passed(self):
        self.stringio.getvalue().should.equal('  PASS: assertion 1\n')

class WhenPrintingVerboselyAndAnAssertionFails(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_10.py', 1, 'made_up_function_1', 'frame1'),
              ('made_up_file_11.py', 2, 'made_up_function_2', 'frame2')]
        self.exception = tools.build_fake_assertion_error(tb, "you fail")
        self.assertion = tools.create_assertion("assertion2")

    def because_an_assertion_fails(self):
        self.reporter.assertion_failed(self.assertion, self.exception)

    def it_should_output_a_stack_trace(self):
        self.stringio.getvalue().should.equal(
"""  FAIL: assertion 2
    Traceback (most recent call last):
      File "made_up_file_10.py", line 1, in made_up_function_1
        frame1
      File "made_up_file_11.py", line 2, in made_up_function_2
        frame2
    test.tools.FakeAssertionError: you fail
""")

class WhenPrintingVerboselyAndAnAssertionErrors(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_12.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_13.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "no")
        self.assertion = tools.create_assertion("assertion3")

    def because_an_assertion_errors(self):
        self.reporter.assertion_errored(self.assertion, self.exception)

    def it_should_output_a_stack_trace(self):
        self.stringio.getvalue().should.equal(
"""  ERROR: assertion 3
    Traceback (most recent call last):
      File "made_up_file_12.py", line 3, in made_up_function_3
        frame3
      File "made_up_file_13.py", line 4, in made_up_function_4
        frame4
    test.tools.FakeException: no
""")

class WhenPrintingVerboselyAndAContextErrors(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_14.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_15.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")
        self.context = tools.create_context("made.up_context_2", ["abc", 123])

    @contexts.action
    def because_a_context_errors(self):
        self.reporter.context_errored(self.context, self.exception)

    def it_should_output_a_stack_trace(self):
        self.stringio.getvalue().should.equal(
"""  Traceback (most recent call last):
    File "made_up_file_14.py", line 3, in made_up_function_3
      frame3
    File "made_up_file_15.py", line 4, in made_up_function_4
      frame4
  test.tools.FakeException: out
""")

class WhenPrintingVerboselyAndAnUnexpectedErrorOccurs(VerboseReporterSharedContext):
    def context(self):
        tb = [('made_up_file_16.py', 3, 'made_up_function_3', 'frame3'),
               ('made_up_file_17.py', 4, 'made_up_function_4', 'frame4')]
        self.exception = tools.build_fake_exception(tb, "out")
    def because_an_unexpected_error_occurs(self):
        self.reporter.unexpected_error(self.exception)
    def it_should_output_a_stack_trace(self):
        self.stringio.getvalue().should.equal(
"""Traceback (most recent call last):
  File "made_up_file_16.py", line 3, in made_up_function_3
    frame3
  File "made_up_file_17.py", line 4, in made_up_function_4
    frame4
test.tools.FakeException: out
""")
