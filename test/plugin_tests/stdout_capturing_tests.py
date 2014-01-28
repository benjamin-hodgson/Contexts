import sys
from io import StringIO
import contexts
from contexts import plugins
from contexts.plugins.decorators import action
from . import tools


class StdOutCapturingSharedContext:
    def shared_context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

        self.stringio = StringIO()
        self.reporter = plugins.cli.StdOutCapturingReporter(self.stringio)

    def cleanup_stdout_and_stderr(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

class WhenCapturingStdOutAndATestPasses(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")

    def because_the_assertion_passes(self):
        self.reporter.context_started(self.ctx.name, self.ctx.example)
        print("passing context")
        self.reporter.assertion_started("assertion")
        print("passing assertion")
        print("to stderr", file=sys.stderr)
        self.reporter.assertion_passed("assertion")
        self.reporter.context_ended(self.ctx.name, self.ctx.example)

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_let_stderr_through(self):
        assert self.fake_stderr.getvalue() == "to stderr\n"

    def it_should_not_output_the_captured_stdout(self):
        assert self.stringio.getvalue() == ("""\
context
  PASS: assertion
""")

class WhenCapturingStdOutAndATestFails(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")

    def because_the_test_fails_and_we_print_something(self):
        self.reporter.context_started(self.ctx.name, self.ctx.example)
        print("failing context")
        self.reporter.assertion_started("assertion")
        print("failing assertion")
        self.reporter.assertion_failed("assertion", tools.FakeAssertionError())
        self.reporter.context_ended(self.ctx.name, self.ctx.example)

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_output_the_captured_stdout(self):
        assert self.stringio.getvalue() == ("""\
context
  FAIL: assertion
    plugin_tests.tools.FakeAssertionError
    ------------------ >> begin captured stdout << -------------------
    failing context
    failing assertion
    ------------------- >> end captured stdout << --------------------
""")

class WhenCapturingStdOutAndATestErrors(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")

    def because_the_test_errors_and_we_print_something(self):
        self.reporter.context_started(self.ctx.name, self.ctx.example)
        print("failing context")
        self.reporter.assertion_started("assertion")
        print("erroring assertion")
        self.reporter.assertion_errored("assertion", tools.FakeException())
        self.reporter.context_ended(self.ctx.name, self.ctx.example)

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_output_the_captured_stdout(self):
        assert self.stringio.getvalue() == ("""\
context
  ERROR: assertion
    plugin_tests.tools.FakeException
    ------------------ >> begin captured stdout << -------------------
    failing context
    erroring assertion
    ------------------- >> end captured stdout << --------------------
""")

class WhenCapturingStdOutAndAContextErrors(StdOutCapturingSharedContext):
    def establish_that_we_have_printed_something(self):
        self.ctx = tools.create_context("context")
        self.reporter.context_started(self.ctx.name, self.ctx.example)
        print("erroring context")
        self.reporter.assertion_started("assertion")
        print("assertion in erroring context")
        self.reporter.assertion_passed("assertion")

    @action
    def because_the_context_errors(self):
        self.reporter.context_errored(self.ctx.name, self.ctx.example, tools.FakeException())

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_output_the_captured_stdout(self):
        assert self.stringio.getvalue() == ("""\
context
  PASS: assertion
  plugin_tests.tools.FakeException
  ------------------- >> begin captured stdout << --------------------
  erroring context
  assertion in erroring context
  -------------------- >> end captured stdout << ---------------------
""")

class WhenCapturingStdOutButNotPrinting(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion_name = "assertion_name"

    def because_an_assertion_fails_but_we_dont_print(self):
        self.reporter.context_started(self.ctx.name, self.ctx.example)
        self.reporter.assertion_started(self.assertion_name)
        # don't print anything
        self.reporter.assertion_failed(self.assertion_name, tools.FakeAssertionError())
        self.reporter.context_ended(self.ctx.name, self.ctx.example)

    def it_should_not_print_anything_to_stdout(self):
        assert self.fake_stdout.getvalue() == ''

    def it_should_not_output_the_delimiters(self):
        assert self.stringio.getvalue() == ("""\
context
  FAIL: assertion name
    plugin_tests.tools.FakeAssertionError
""")
