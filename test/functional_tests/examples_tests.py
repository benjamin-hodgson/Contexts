import types
import contexts
from .tools import SpyReporter
from contexts.configuration import NullConfiguration


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

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, [], config=NullConfiguration())

    def it_should_instantiate_the_class_twice(self):
        assert self.ParametrisedSpec.initialised == 2

    def it_should_run_the_setup_twice(self):
        assert self.ParametrisedSpec.setups == [1,2]

    def it_should_run_the_assertion_twice(self):
        assert self.ParametrisedSpec.assertions == [1,2]

    def it_should_run_the_action_twice(self):
        assert self.ParametrisedSpec.actions == [1,2]

    def it_should_run_the_teardown_twice(self):
        assert self.ParametrisedSpec.teardowns == [1,2]


class WhenRunningAParametrisedSpecAndExamplesYieldsTuples:
    def given_a_parametrised_test(self):
        class ParametrisedSpec:
            params = []
            @classmethod
            def has_examples_in_the_name(cls):
                yield 1, 2
                yield 3, 4
            def it(self, a, b):
                self.__class__.params.append(a)
                self.__class__.params.append(b)
        self.ParametrisedSpec = ParametrisedSpec

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, [], config=NullConfiguration())

    def it_should_unpack_the_tuples(self):
        assert self.ParametrisedSpec.params == [1,2,3,4]


class WhenRunningAParametrisedSpecAndExamplesYieldsTuplesButTheMethodsOnlyAcceptOneArgument:
    def given_a_parametrised_test(self):
        class ParametrisedSpec:
            params = []
            @classmethod
            def has_examples_in_the_name(cls):
                yield 1, 2
                yield 3, 4
            def it(self, a):
                self.__class__.params.append(a)
        self.ParametrisedSpec = ParametrisedSpec

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, [], config=NullConfiguration())

    def it_should_run_the_setup_twice(self):
        assert self.ParametrisedSpec.params == [(1,2),(3,4)]


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

    def because_we_run_the_class(self):
        contexts.run(self.ParametrisedSpec, [], config=NullConfiguration())

    def it_should_instantiate_the_class_twice(self):
        assert self.ParametrisedSpec.initialised == 2

    def it_should_run_the_setup_twice(self):
        assert self.ParametrisedSpec.setups == 2

    def it_should_run_the_action_twice(self):
        assert self.ParametrisedSpec.actions == 2

    def it_should_run_the_assertion_twice(self):
        assert self.ParametrisedSpec.assertions == 2

    def it_should_run_the_teardown_twice(self):
        assert self.ParametrisedSpec.teardowns == 2


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

    def because_we_run_the_module(self):
        contexts.run(self.module, [], config=NullConfiguration())

    def it_should_instantiate_the_class_twice(self):
        assert self.ParametrisedSpec.initialised == 2

    def it_should_run_the_setup_twice(self):
        assert self.ParametrisedSpec.setups == [1,2]

    def it_should_run_the_action_twice(self):
        assert self.ParametrisedSpec.actions == [1,2]

    def it_should_run_the_assertion_twice(self):
        assert self.ParametrisedSpec.assertions == [1,2]

    def it_should_run_the_teardown_twice(self):
        assert self.ParametrisedSpec.teardowns == [1,2]


class WhenExamplesRaisesAnException:
    def context(self):
        self.exception = Exception()
        class TestSpec:
            total = 0
            @classmethod
            def examples(s):
                yield 3
                raise self.exception
            def it(s, example):
                s.__class__.total += example
        self.spec = TestSpec
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [self.reporter], config=NullConfiguration())

    def it_should_run_the_first_one(self):
        assert self.spec.total == 3

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.reporter.calls[-3][0] == "unexpected_error"

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[-3][1] == self.exception


class WhenUserFailsToMakeExamplesAClassmethod:
    def context(self):
        class Naughty:
            def examples(self):
                pass
        self.spec = Naughty
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [self.reporter], config=NullConfiguration())

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.reporter.calls[2][0] == "unexpected_error"

    def it_should_pass_in_a_TypeError(self):
        assert isinstance(self.reporter.calls[2][1], TypeError)

    def it_should_finish_the_test_run(self):
        assert self.reporter.calls[-1][0] == "test_run_ended"


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
        contexts.run(self.spec, [], config=NullConfiguration())

    def it_should_run_the_spec_once(self):
        assert self.spec.times_run == 1
