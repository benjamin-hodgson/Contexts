from unittest import mock
from .tools import run_object
from contexts.plugin_interface import PluginInterface, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts import assertion


class WhenRunningAParametrisedSpec:
    def given_a_parametrised_test(self):
        class ParametrisedSpec:
            initialised = 0
            setups = []
            actions = []
            assertions = []
            teardowns = []
            @classmethod
            def examples(cls):
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

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.context: SETUP,
            ParametrisedSpec.because: ACTION,
            ParametrisedSpec.it: ASSERTION,
            ParametrisedSpec.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_class(self):
        run_object(self.ParametrisedSpec, [self.plugin])

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
            def examples(cls):
                yield 1, 2
                yield 3, 4
            def it(self, a, b):
                self.__class__.params.append(a)
                self.__class__.params.append(b)
        self.ParametrisedSpec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_class(self):
        run_object(self.ParametrisedSpec, [self.plugin])

    def it_should_unpack_the_tuples(self):
        assert self.ParametrisedSpec.params == [1,2,3,4]


class WhenRunningAParametrisedSpecAndExamplesYieldsTuplesButTheMethodsOnlyAcceptOneArgument:
    def given_a_parametrised_test(self):
        class ParametrisedSpec:
            params = []
            @classmethod
            def examples(cls):
                yield 1, 2
                yield 3, 4
            def it(self, a):
                self.__class__.params.append(a)
        self.ParametrisedSpec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_class(self):
        run_object(self.ParametrisedSpec, [self.plugin])

    def it_should_not_unpack_the_tuples(self):
        assert self.ParametrisedSpec.params == [(1,2), (3,4)]


class WhenRunningAParametrisedSpecWithNonParametrisedMethods:
    def context(self):
        class ParametrisedSpec:
            initialised = 0
            setups = 0
            actions = 0
            assertions = 0
            teardowns = 0
            @classmethod
            def examples(cls):
                yield 1
                yield 2
            def it(self):
                self.__class__.assertions += 1
        self.ParametrisedSpec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_class(self):
        run_object(self.ParametrisedSpec, [self.plugin])

    def it_should_run_the_assertion_twice(self):
        assert self.ParametrisedSpec.assertions == 2


class WhenNotifyingAPluginOfExamples:
    def context(self):
        class ParametrisedSpec:
            @classmethod
            def examples(cls):
                yield 1
                yield 2
            def it(self):
                pass
        self.ParametrisedSpec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_class(self):
        run_object(self.ParametrisedSpec, [self.plugin])

    def it_should_call_test_class_started_once(self):
        assert self.plugin.mock_calls[3] == mock.call.test_class_started(self.ParametrisedSpec)
        assert self.plugin.test_class_started.call_count == 1

    @assertion
    def it_should_call_context_started_with_the_first_example(self):
        assert self.plugin.context_started.mock_calls[0] == mock.call("ParametrisedSpec", 1)

    @assertion
    def it_should_call_context_ended_with_the_first_example(self):
        assert self.plugin.context_ended.mock_calls[0] == mock.call("ParametrisedSpec", 1)

    @assertion
    def it_should_call_context_started_with_the_second_example(self):
        assert self.plugin.context_started.mock_calls[1] == mock.call("ParametrisedSpec", 2)

    @assertion
    def it_should_call_context_ended_with_the_first_example(self):
        assert self.plugin.context_ended.mock_calls[1] == mock.call("ParametrisedSpec", 2)

    def it_should_call_test_class_ended_once(self):
        assert self.plugin.mock_calls[-3] == mock.call.test_class_ended(self.ParametrisedSpec)
        assert self.plugin.test_class_ended.call_count == 1



class WhenExamplesRaisesAnException:
    def context(self):
        self.exception = Exception()
        class ParametrisedSpec:
            total = 0
            @classmethod
            def examples(s):
                yield 3
                raise self.exception
            def it(s, example):
                s.__class__.total += example
        self.spec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_run_the_first_one(self):
        assert self.spec.total == 3

    def it_should_send_an_exception_to_the_plugin(self):
        self.plugin.unexpected_error.assert_called_once_with(self.exception)


class WhenUserFailsToMakeExamplesAClassmethod:
    def context(self):
        class Naughty:
            def examples(self):
                pass
            def it(self):
                pass
        self.spec = Naughty

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            Naughty.examples: EXAMPLES,
            Naughty.it: ASSERTION
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.plugin.unexpected_error.called

    def it_should_pass_in_a_TypeError(self):
        assert isinstance(self.plugin.unexpected_error.call_args[0][0], TypeError)


class WhenExamplesReturnsNone:
    def context(self):
        class ParametrisedSpec:
            times_run = 0
            @classmethod
            def examples(cls):
                pass
            def it(self):
                self.__class__.times_run += 1
        self.spec = ParametrisedSpec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            ParametrisedSpec.examples: EXAMPLES,
            ParametrisedSpec.it: ASSERTION
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_run_the_spec_once(self):
        assert self.spec.times_run == 1
