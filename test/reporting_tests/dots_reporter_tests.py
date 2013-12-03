from io import StringIO
import sure
from contexts import reporting
from .. import tools


class DotsReporterSharedContext:
    def context(self):
        self.stringio = StringIO()
        self.reporter = reporting.cli.DotsReporter(self.stringio)

class WhenWatchingForDotsAndAnAssertionPasses(DotsReporterSharedContext):
    def because_an_assertion_passes(self):
        self.reporter.assertion_passed(tools.create_assertion())
    def it_should_print_a_dot(self):
        self.stringio.getvalue().should.equal('.')

class WhenWatchingForDotsAndAnAssertionFails(DotsReporterSharedContext):
    def because_an_assertion_fails(self):
        self.reporter.assertion_failed(tools.create_assertion(), AssertionError())
    def it_should_print_an_F(self):
        self.stringio.getvalue().should.equal('F')

class WhenWatchingForDotsAndAnAssertionErrors(DotsReporterSharedContext):
    def because_an_assertion_errors(self):
        self.reporter.assertion_errored(tools.create_assertion(), Exception())
    def it_should_print_an_E_for_the_error(self):
        self.stringio.getvalue().should.equal('E')

class WhenWatchingForDotsAndAContextErrors(DotsReporterSharedContext):
    def because_an_assertion_fails(self):
        self.reporter.context_errored(tools.create_context(), Exception())
    def it_should_print_an_E_for_the_error(self):
        self.stringio.getvalue().should.equal('E')

class WhenWatchingForDotsAndAnUnexpectedErrorOccurs(DotsReporterSharedContext):
    def because_an_assertion_fails(self):
        self.reporter.unexpected_error(Exception())
    def it_should_print_an_E_for_the_error(self):
        self.stringio.getvalue().should.equal('E')
