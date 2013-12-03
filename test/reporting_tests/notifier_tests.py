import sure
from contexts.reporting.shared import ReporterNotifier
from .. import tools

# I think, if the other tests stop using the notifier, this file won't be necessary - 
# the core tests have already proved that the correct reporter methods get called

class NotifierSharedContext:
    def establish_that_the_notifier_contains_mocks(self):
        self.mock_reporter1 = tools.MockReporter()
        self.mock_reporter2 = tools.MockReporter()

        self.notifier = ReporterNotifier(self.mock_reporter1, self.mock_reporter2)

class WhenUsingRunSuite(NotifierSharedContext):
    def establish(self):
        self.suite = tools.create_suite()

    def because_everything_goes_well(self):
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

class WhenUsingRunSuiteAndAnErrorOccurs(NotifierSharedContext):
    def establish(self):
        self.suite = tools.create_suite()
        self.exception = Exception()

    def because_an_exception_gets_raised(self):
        with self.notifier.run_suite(self.suite):
            raise self.exception

    def it_should_call_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.exception)

    def it_should_call_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.exception)

    def it_should_still_call_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[2][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[2][1].should.equal(self.suite)

    def it_should_still_call_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[2][0].should.equal("suite_ended")

    def it_should_pass_the_suite_into_suite_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[2][1].should.equal(self.suite)

class WhenUsingImportingAndAnErrorOccurs(NotifierSharedContext):
    # this is used to catch unexpected errors when importing a module
    def establish(self):
        self.module_spec = ('a', 'b')
        self.exception = Exception()

    def because_an_exception_gets_raised(self):
        with self.notifier.importing(self.module_spec):
            raise self.exception

    def it_should_call_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[0][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[0][1].should.equal(self.exception)

    def it_should_call_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[0][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[0][1].should.equal(self.exception)

class WhenUsingRunClassAndAnErrorOccurs(NotifierSharedContext):
    # this is used to catch unexpected errors when getting examples/instantiating a class
    def establish(self):
        class Spec:
            pass
        self.cls = Spec
        self.exception = Exception()

    def because_an_exception_gets_raised(self):
        with self.notifier.run_class(self.cls):
            raise self.exception

    def it_should_call_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[0][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_first_mock(self):
        self.mock_reporter1.calls[0][1].should.equal(self.exception)

    def it_should_call_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[0][0].should.equal("unexpected_error")

    def it_should_pass_the_exception_into_unexpected_error_on_the_second_mock(self):
        self.mock_reporter2.calls[0][1].should.equal(self.exception)

class WhenUsingRunContext(NotifierSharedContext):
    def establish(self):
        self.context = tools.create_context('')

    def because_everything_goes_smoothly(self):
        with self.notifier.run_context(self.context):
            pass

    def it_should_call_ctx_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][0].should.equal("context_started")

    def it_should_pass_the_ctx_into_ctx_started_on_the_first_mock(self):
        self.mock_reporter1.calls[0][1].should.equal(self.context)

    def it_should_call_ctx_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][0].should.equal("context_started")

    def it_should_pass_the_ctx_into_ctx_started_on_the_second_mock(self):
        self.mock_reporter2.calls[0][1].should.equal(self.context)

    def it_should_call_ctx_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("context_ended")

    def it_should_pass_the_ctx_into_ctx_ended_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.context)

    def it_should_call_ctx_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("context_ended")

    def it_should_pass_the_ctx_into_ctx_ended_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.context)

class WhenUsingRunContextAndAnErrorOccurs(NotifierSharedContext):
    def establish(self):
        self.context = tools.create_context('')
        self.exception = Exception()

    def because_an_exception_gets_raised(self):
        with self.notifier.run_context(self.context):
            raise self.exception

    def it_should_call_ctx_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("context_errored")

    def it_should_pass_the_ctx_into_ctx_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.context)

    def it_should_pass_the_exception_into_ctx_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[1][2].should.equal(self.exception)

    def it_should_call_ctx_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("context_errored")

    def it_should_pass_the_ctx_into_ctx_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.context)

    def it_should_pass_the_exception_into_ctx_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[1][2].should.equal(self.exception)

class WhenUsingRunAssertion(NotifierSharedContext):
    def establish(self):
        self.context = tools.create_context('')
        self.assertion = tools.create_assertion('')

    def because_everything_goes_smoothly(self):
        with self.notifier.run_context(self.context):
            with self.notifier.run_assertion(self.assertion):
                pass

    def it_should_call_assertion_started_on_the_first_mock(self):
        self.mock_reporter1.calls[1][0].should.equal("assertion_started")

    def it_should_pass_the_assertion_into_assertion_started_on_the_first_mock(self):
        self.mock_reporter1.calls[1][1].should.equal(self.assertion)

    def it_should_call_assertion_started_on_the_second_mock(self):
        self.mock_reporter2.calls[1][0].should.equal("assertion_started")

    def it_should_pass_the_assertion_into_assertion_started_on_the_second_mock(self):
        self.mock_reporter2.calls[1][1].should.equal(self.assertion)

    def it_should_call_assertion_passed_on_the_first_mock(self):
        self.mock_reporter1.calls[2][0].should.equal("assertion_passed")

    def it_should_pass_the_assertion_into_assertion_passed_on_the_first_mock(self):
        self.mock_reporter1.calls[2][1].should.equal(self.assertion)

    def it_should_call_assertion_passed_on_the_second_mock(self):
        self.mock_reporter2.calls[2][0].should.equal("assertion_passed")

    def it_should_pass_the_assertion_into_assertion_passed_on_the_second_mock(self):
        self.mock_reporter2.calls[2][1].should.equal(self.assertion)

class WhenUsingRunAssertionAndItFails(NotifierSharedContext):
    def establish(self):
        self.context = tools.create_context('')
        self.assertion = tools.create_assertion('')
        self.exception = AssertionError()

    def because_everything_goes_smoothly(self):
        with self.notifier.run_context(self.context):
            with self.notifier.run_assertion(self.assertion):
                raise self.exception

    def it_should_call_assertion_failed_on_the_first_mock(self):
        self.mock_reporter1.calls[2][0].should.equal("assertion_failed")

    def it_should_pass_the_assertion_into_assertion_failed_on_the_first_mock(self):
        self.mock_reporter1.calls[2][1].should.equal(self.assertion)

    def it_should_pass_the_exception_into_assertion_failed_on_the_first_mock(self):
        self.mock_reporter1.calls[2][2].should.equal(self.exception)

    def it_should_call_assertion_failed_on_the_second_mock(self):
        self.mock_reporter2.calls[2][0].should.equal("assertion_failed")

    def it_should_pass_the_assertion_into_assertion_failed_on_the_second_mock(self):
        self.mock_reporter2.calls[2][1].should.equal(self.assertion)

    def it_should_pass_the_exception_into_assertion_failed_on_the_second_mock(self):
        self.mock_reporter2.calls[2][2].should.equal(self.exception)

class WhenUsingRunAssertionAndItErrors(NotifierSharedContext):
    def establish(self):
        self.context = tools.create_context('')
        self.assertion = tools.create_assertion('')
        self.exception = Exception()

    def because_everything_goes_smoothly(self):
        with self.notifier.run_context(self.context):
            with self.notifier.run_assertion(self.assertion):
                raise self.exception

    def it_should_call_assertion_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[2][0].should.equal("assertion_errored")

    def it_should_pass_the_assertion_into_assertion_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[2][1].should.equal(self.assertion)

    def it_should_pass_the_exception_into_assertion_errored_on_the_first_mock(self):
        self.mock_reporter1.calls[2][2].should.equal(self.exception)

    def it_should_call_assertion_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[2][0].should.equal("assertion_errored")

    def it_should_pass_the_assertion_into_assertion_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[2][1].should.equal(self.assertion)

    def it_should_pass_the_exception_into_assertion_errored_on_the_second_mock(self):
        self.mock_reporter2.calls[2][2].should.equal(self.exception)
