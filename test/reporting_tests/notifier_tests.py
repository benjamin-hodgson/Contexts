import sure
from contexts.reporting.shared import ReporterNotifier
from .. import tools

class WhenUsingRunSuite:
    def establish_that_the_notifier_contains_mocks(self):
        self.mock_reporter1 = tools.MockReporter()
        self.mock_reporter2 = tools.MockReporter()

        self.notifier = ReporterNotifier(self.mock_reporter1, self.mock_reporter2)
        self.suite = tools.create_suite()

    def because_we_call_run_suite(self):
        with self.notifier.run_suite(self.suite):
            pass

    def it_should_call_suite_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][0].should.equal("suite_started")

    def it_should_pass_the_suite_into_suite_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][1].should.equal(self.suite)

    def it_should_call_suite_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][0].should.equal("suite_started")

    def it_should_pass_the_suite_into_suite_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][1].should.equal(self.suite)

    def it_should_call_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.suite)

    def it_should_call_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.suite)

class WhenUsingRunSuiteAndAnErrorOccurs:
    def establish_that_the_notifier_contains_mocks(self):
        self.mock_reporter1 = tools.MockReporter()
        self.mock_reporter2 = tools.MockReporter()

        self.notifier = ReporterNotifier(self.mock_reporter1, self.mock_reporter2)
        self.suite = tools.create_suite()
        self.exception = Exception()

    def because_we_call_run_suite(self):
        with self.notifier.run_suite(self.suite):
            raise self.exception

    def it_should_call_suite_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][0].should.equal("suite_started")

    def it_should_pass_the_suite_into_suite_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][1].should.equal(self.suite)

    def it_should_call_suite_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][0].should.equal("suite_started")

    def it_should_pass_the_suite_into_suite_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][1].should.equal(self.suite)

    def it_should_call_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.exception)

    def it_should_call_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.exception)

    def it_should_call_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[2][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[2][1].should.equal(self.suite)

    def it_should_call_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[2][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[2][1].should.equal(self.suite)

