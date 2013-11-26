import types
import sure
import contexts
from .tools import MockReporter


class WhenRunningAParametrisedSpec:
    def given_a_parametrised_test(self):
        class ParametrisedSpec:
            initialised = 0
            setups = []
            actions = []
            assertions = []
            teardowns = []
            @classmethod
            def has_examples_in_the_name(cls):
                yield 1
                yield 2
            def __init__(self):
                self.__class__.initialised += 1
            def context(self, example):
                self.__class__.setups.append(example)
            def because(self, example):
                self.__class__.actions.append(example)
            def it(self, example):
                self.__class__.assertions.append(example)
            def cleanup(self, example):
                self.__class__.teardowns.append(example)
        self.ParametrisedSpec = ParametrisedSpec
        self.reporter = MockReporter()

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, self.reporter)

    def the_ctx_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("context_errored")

    def the_assertions_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_errored")

    def the_assertions_should_not_fail(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_failed")

    def it_should_instantiate_the_class_twice(self):
        self.ParametrisedSpec.initialised.should.equal(2)

    def it_should_run_the_setup_twice(self):
        self.ParametrisedSpec.setups.should.equal([1,2])

    def it_should_run_the_action_twice(self):
        self.ParametrisedSpec.actions.should.equal([1,2])

    def it_should_run_the_teardown_twice(self):
        self.ParametrisedSpec.teardowns.should.equal([1,2])


class WhenRunningAParametrisedSpecWithNonParametrisedMethods:
    def context(self):
        class ParametrisedSpec:
            initialised = 0
            setups = 0
            actions = 0
            assertions = 0
            teardowns = 0
            @classmethod
            def has_examples_in_the_name(cls):
                yield 1
                yield 2
            def __init__(self):
                self.__class__.initialised += 1
            def context(self):
                self.__class__.setups += 1
            def because(self):
                self.__class__.actions += 1
            def it(self):
                self.__class__.assertions += 1
            def cleanup(self):
                self.__class__.teardowns += 1
        self.ParametrisedSpec = ParametrisedSpec
        self.reporter = MockReporter()

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, self.reporter)

    def the_ctx_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("context_errored")

    def the_assertions_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_errored")

    def the_assertions_should_not_fail(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_failed")

    def it_should_instantiate_the_class_twice(self):
        self.ParametrisedSpec.initialised.should.equal(2)

    def it_should_run_the_setup_twice(self):
        self.ParametrisedSpec.setups.should.equal(2)

    def it_should_run_the_action_twice(self):
        self.ParametrisedSpec.actions.should.equal(2)

    def it_should_run_the_teardown_twice(self):
        self.ParametrisedSpec.teardowns.should.equal(2)


class WhenRunningAModuleWithParametrisedSpecs:
    def context(self):
        class ParametrisedSpec:
            initialised = 0
            setups = []
            actions = []
            assertions = []
            teardowns = []
            @classmethod
            def has_examples_in_the_name(cls):
                yield 1
                yield 2
            def __init__(self):
                self.__class__.initialised += 1
            def context(self, example):
                self.__class__.setups.append(example)
            def because(self, example):
                self.__class__.actions.append(example)
            def it(self, example):
                self.__class__.assertions.append(example)
            def cleanup(self, example):
                self.__class__.teardowns.append(example)
        self.module = types.ModuleType('fake_specs')
        self.ParametrisedSpec = ParametrisedSpec
        self.module.ParametrisedSpec = ParametrisedSpec
        self.reporter = MockReporter()

    def because_we_run_the_module(self):
        contexts.run(self.module, self.reporter)

    def the_ctx_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("context_errored")

    def the_assertions_should_not_error(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_errored")

    def the_assertions_should_not_fail(self):
        call_names = [call[0] for call in self.reporter.calls]
        call_names.should_not.contain("assertion_failed")

    def it_should_instantiate_the_class_twice(self):
        self.ParametrisedSpec.initialised.should.equal(2)

    def it_should_run_the_setup_twice(self):
        self.ParametrisedSpec.setups.should.equal([1,2])

    def it_should_run_the_action_twice(self):
        self.ParametrisedSpec.actions.should.equal([1,2])

    def it_should_run_the_teardown_twice(self):
        self.ParametrisedSpec.teardowns.should.equal([1,2])


class WhenExamplesRaisesAnException:
    def context(self):
        self.raised = Exception()
        class TestSpec:
            total = 0
            @classmethod
            def examples(s):
                yield 3
                raise self.raised
            def it(s, example):
                s.__class__.total += example
        self.spec = TestSpec
        self.reporter = MockReporter()

    def because_we_run_the_spec(self):
        self.exception = contexts.catch(contexts.run, self.spec, self.reporter)

    def it_should_not_throw_an_exception(self):
        self.exception.should.be.none

    def it_should_run_the_first_one(self):
        self.spec.total.should.equal(3)

    def it_should_call_unexpected_error_on_the_reporter(self):
        self.reporter.calls[-2][0].should.equal("unexpected_error")

    def it_should_pass_in_the_exception(self):
        self.reporter.calls[-2][1].should.equal(self.raised)


class WhenUserFailsToMakeExamplesAClassmethod:
    def context(self):
        class Naughty:
            def examples(self):
                pass
        self.spec = Naughty
        self.reporter = MockReporter()

    def because_we_run_the_spec(self):
        self.exception = contexts.catch(contexts.run, self.spec, self.reporter)

    def it_should_not_throw_an_exception(self):
        self.exception.should.be.none

    def it_should_call_unexpected_error_on_the_reporter(self):
        self.reporter.calls[1][0].should.equal("unexpected_error")

    def it_should_pass_in_a_TypeError(self):
        self.reporter.calls[1][1].should.be.a(TypeError)

    def it_should_finish_the_suite(self):
        self.reporter.calls[-1][0].should.equal("suite_ended")


class WhenExamplesReturnsNone:
    def context(self):
        class Spec:
            times_run = 0
            @classmethod
            def examples(cls):
                pass
            def it(self):
                self.__class__.times_run += 1
        self.spec = Spec

    def because_we_run_the_spec(self):
        self.exception = contexts.catch(contexts.run, self.spec, MockReporter())

    def it_should_not_throw_an_exception(self):
        self.exception.should.be.none

    def it_should_run_the_spec_once(self):
        self.spec.times_run.should.equal(1)


if __name__ == "__main__":
    contexts.run()
