import sys
from io import StringIO
import sure
from contexts import reporting
from .. import tools


class StdOutCapturingSharedContext:
    def shared_context(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = self.fake_stdout = StringIO()
        sys.stderr = self.fake_stderr = StringIO()

        self.stringio = StringIO()
        self.reporter = reporting.cli.StdOutCapturingReporter(self.stringio)

    def cleanup_stdout_and_stderr(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

class WhenCapturingStdOutAndATestPasses(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion = tools.create_assertion("assertion")

    def because_the_assertion_passes(self):
        self.reporter.context_started(self.ctx)
        print("passing context")
        self.reporter.assertion_started(self.assertion)
        print("passing assertion")
        print("to stderr", file=sys.stderr)
        self.reporter.assertion_passed(self.assertion)
        self.reporter.context_ended(self.ctx)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_let_stderr_through(self):
        self.fake_stderr.getvalue().should.equal("to stderr\n")

    def it_should_not_output_the_captured_stdout(self):
        self.stringio.getvalue().should.equal("""\
context
  PASS: assertion
""")

class WhenCapturingStdOutAndATestFails(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion = tools.create_assertion("assertion")

    def because_the_test_fails_and_we_print_something(self):
        self.reporter.context_started(self.ctx)
        print("failing context")
        self.reporter.assertion_started(self.assertion)
        print("failing assertion")
        self.reporter.assertion_failed(self.assertion, tools.FakeAssertionError())
        self.reporter.context_ended(self.ctx)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_output_the_captured_stdout(self):
        self.stringio.getvalue().should.equal("""\
context
  FAIL: assertion
    test.tools.FakeAssertionError
    ------------------ >> begin captured stdout << -------------------
    failing context
    failing assertion
    ------------------- >> end captured stdout << --------------------
""")

class WhenCapturingStdOutAndATestErrors(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion = tools.create_assertion("assertion")

    def because_the_test_errors_and_we_print_something(self):
        self.reporter.context_started(self.ctx)
        print("failing context")
        self.reporter.assertion_started(self.assertion)
        print("erroring assertion")
        self.reporter.assertion_errored(self.assertion, tools.FakeException())
        self.reporter.context_ended(self.ctx)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_output_the_captured_stdout(self):
        self.stringio.getvalue().should.equal("""\
context
  ERROR: assertion
    test.tools.FakeException
    ------------------ >> begin captured stdout << -------------------
    failing context
    erroring assertion
    ------------------- >> end captured stdout << --------------------
""")

class WhenCapturingStdOutAndAContextErrors(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion = tools.create_assertion("assertion")

    def because_the_ctx_errors_and_we_print_something(self):
        self.reporter.context_started(self.ctx)
        print("erroring context")
        self.reporter.assertion_started(self.assertion)
        print("assertion in erroring context")
        self.reporter.assertion_passed(self.assertion)
        self.reporter.context_errored(self.ctx, tools.FakeException())

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_output_the_captured_stdout(self):
        self.stringio.getvalue().should.equal("""\
context
  PASS: assertion
  test.tools.FakeException
  ------------------- >> begin captured stdout << --------------------
  erroring context
  assertion in erroring context
  -------------------- >> end captured stdout << ---------------------
""")

class WhenCapturingStdOutButNotPrinting(StdOutCapturingSharedContext):
    def context(self):
        self.ctx = tools.create_context("context")
        self.assertion = tools.create_assertion("assertion")

    def because_an_assertion_fails_but_we_dont_print(self):
        self.reporter.context_started(self.ctx)
        self.reporter.assertion_started(self.assertion)
        # don't print anything
        self.reporter.assertion_failed(self.assertion, tools.FakeAssertionError())
        self.reporter.context_ended(self.ctx)

    def it_should_not_print_anything_to_stdout(self):
        self.fake_stdout.getvalue().should.be.empty

    def it_should_not_output_the_delimiters(self):
        self.stringio.getvalue().should.equal("""\
context
  FAIL: assertion
    test.tools.FakeAssertionError
""")
