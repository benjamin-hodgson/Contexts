import collections.abc
from unittest import mock
import contexts
from contexts.plugin_interface import PluginInterface, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN, NO_EXAMPLE
from contexts.plugins.identification import NameBasedIdentifier
from contexts import assertion
from .tools import SpyReporter, UnorderedList, run_object


core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenAPluginSuppliesAClassToRun:
    def context(self):
        self.ran_method = False
        class TestSpec:
            def method(s):
                self.ran_method = True
        self.spec = TestSpec
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.get_object_to_run.return_value = TestSpec
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_with_the_plugin(self):
        contexts.run_with_plugins([self.plugin])

    def it_should_run_the_method(self):
        assert self.ran_method


class WhenAPluginIdentifiesMethods:
    def context(self):
        self.log = []
        class TestSpec:
            @classmethod
            def method_zero(cls):
                self.log.append("examples")
                yield 1
                yield 2
            def method_one(s, example):
                self.log.append(("setup",example))
            def method_two(s, example):
                self.log.append(("action",example))
            def method_three(s, example):
                self.log.append(("assertion",example))
            def method_four(s, example):
                self.log.append(("teardown",example))
        self.spec = TestSpec

        self.none_plugin = mock.Mock(spec=PluginInterface)
        self.none_plugin.identify_method.return_value = None

        self.deleted_plugin = mock.Mock(spec=PluginInterface)
        del self.deleted_plugin.identify_method

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            TestSpec.method_zero: EXAMPLES,
            TestSpec.method_one: SETUP,
            TestSpec.method_two: ACTION,
            TestSpec.method_three: ASSERTION,
            TestSpec.method_four: TEARDOWN
        }[meth]

        self.too_late_plugin = mock.Mock(spec=PluginInterface)


    def because_we_run_the_spec(self):
        run_object(self.spec, [self.none_plugin, self.deleted_plugin, self.plugin, self.too_late_plugin])

    def it_should_not_ask_the_plugin_to_identify_the_class(self):
        # we are explicitly running this class, don't want to give plugs a chance to stop it
        pass

    def it_should_ask_the_plugin_to_identify_each_method(self):
        self.plugin.identify_method.assert_has_calls([
                mock.call(self.spec.method_zero),
                mock.call(self.spec.method_one),
                mock.call(self.spec.method_two),
                mock.call(self.spec.method_three),
                mock.call(self.spec.method_four)
            ], any_order=True)

    def it_should_not_ask_the_one_that_was_too_late(self):
        assert not self.too_late_plugin.identify_method.called

    def it_should_run_the_supplied_methods_in_the_correct_order(self):
        assert self.log == [
            "examples",
            ("setup", 1),
            ("action", 1),
            ("assertion", 1),
            ("teardown", 1),
            ("setup", 2),
            ("action", 2),
            ("assertion", 2),
            ("teardown", 2)
        ]


class WhenAPluginIdentifiesMultipleAssertions:
    def establish_that_the_plugin_identifies_two_assertions(self):
        self.log = []
        class Spec:
            def method_one(s):
                self.log.append('assertion')
            def method_two(s):
                self.log.append('assertion')
        self.spec = Spec
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_run_both_assertions(self):
        assert self.log == ["assertion", "assertion"]


class WhenAPluginRefusesToIdentifyAMethod:
    def establish_that_the_plugin_returns_none(self):
        self.log = []
        class Spec:
            def method_one(s):
                self.log.append("should not happen")
        self.spec = Spec
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.return_value = None

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_ignore_the_method(self):
        assert self.log == []


class WhenASpecHasASuperclassAndAPluginIdentifiesMethods:
    def establish_spec_with_superclass(self):
        self.log = []
        class Super:
            @classmethod
            def method_zero(s):
                self.log.append("super examples")
            def method_one(s):
                self.log.append("super setup")
            def method_two(s):
                self.log.append("super action")
            def method_three(s):
                self.log.append("super assertion")
            def method_four(s):
                self.log.append("super teardown")
        class Spec(Super):
            @classmethod
            def method_zero_point_five(s):
                self.log.append("sub examples")
                yield 1
            def method_five(s):
                self.log.append("sub setup")
            def method_six(s):
                self.log.append("sub action")
            def method_seven(s):
                self.log.append("sub assertion")
            def method_eight(s):
                self.log.append("sub teardown")
        self.super = Super
        self.spec = Spec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            Super.method_zero: EXAMPLES,
            Super.method_one: SETUP,
            Super.method_two: ACTION,
            Super.method_three: ASSERTION,
            Super.method_four: TEARDOWN,
            Spec.method_zero_point_five: EXAMPLES,
            Spec.method_five: SETUP,
            Spec.method_six: ACTION,
            Spec.method_seven: ASSERTION,
            Spec.method_eight: TEARDOWN
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_identify_method_with_the_superclass_methods_first(self):
        assert self.plugin.identify_method.call_args_list[:5] == UnorderedList([
            mock.call(self.super.method_zero),
            mock.call(self.super.method_one),
            mock.call(self.super.method_two),
            mock.call(self.super.method_three),
            mock.call(self.super.method_four)
        ])

    @assertion
    def it_should_run_the_subclass_examples_before_anything_else(self):
        assert self.log[0] == "sub examples"

    @assertion
    def it_should_not_run_the_superclass_examples(self):
        assert "super examples" not in self.log

    def it_should_run_the_superclass_setup_before_the_subclass_setup(self):
        assert self.log[1:3] == ["super setup", "sub setup"]

    def it_should_run_the_subclass_action_next(self):
        assert self.log[3] == "sub action"

    def it_should_not_run_the_superclass_action(self):
        assert "super action" not in self.log

    def it_should_run_the_subclass_assertions(self):
        assert self.log[4] == "sub assertion"

    def it_should_not_run_the_superclass_assertions(self):
        assert "super assertion" not in self.log

    def it_should_run_the_subclass_teardown_before_the_superclass_teardown(self):
        assert self.log[-2:] == ["sub teardown", "super teardown"]


class WhenAPluginReturnsMultipleMethodsOfTheSameType:
    @classmethod
    def examples_of_ways_plugins_can_mess_up(cls):
        yield [EXAMPLES, EXAMPLES]
        yield [SETUP, SETUP]
        yield [ACTION, ACTION]
        yield [TEARDOWN, TEARDOWN]

    def context(self, side_effect):
        self.ran_a_method = False
        class Spec:
            def method_one(s):
                self.ran_a_method = True
            def method_two(s):
                self.ran_a_method = True
        self.spec = Spec

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = side_effect

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_unexpected_error_with_a_TooManySpecialMethodsError(self):
        assert isinstance(self.plugin.unexpected_error.call_args[0][0], contexts.errors.TooManySpecialMethodsError)

    def it_should_not_run_the_methods(self):
        assert not self.ran_a_method


class WhenRunningASpecWithReporters:
    def context(self):
        class TestSpec:
            log = ""
            def method_with_establish_in_the_name(s):
                s.__class__.log += "arrange "
            def method_with_because_in_the_name(s):
                s.__class__.log += "act "
            def method_with_should_in_the_name(s):
                s.__class__.log += "assert "
            def method_with_cleanup_in_the_name(s):
                s.__class__.log += "teardown "

        self.spec = TestSpec

        self.reporter1 = SpyReporter()
        self.reporter2 = SpyReporter()
        self.reporter3 = SpyReporter()

    def because_we_run_the_spec(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter1, self.reporter2, self.reporter3])

    def it_should_call_test_run_started_first(self):
        assert self.reporter1.calls[0][0] == 'test_run_started'

    @assertion
    def it_should_call_context_started_next(self):
        assert self.reporter1.calls[1][0] == 'context_started'
    @assertion
    def it_should_pass_in_the_context_name(self):
        assert self.reporter1.calls[1][1] == 'TestSpec'
    @assertion
    def it_should_pass_in_no_example(self):
        assert self.reporter1.calls[1][2] is NO_EXAMPLE

    def it_should_call_assertion_started_for_the_assertion(self):
        assert self.reporter1.calls[2][0] == 'assertion_started'
    def it_should_pass_the_assertion_name_into_assertion_started(self):
        assert self.reporter1.calls[2][1] == 'method_with_should_in_the_name'

    def it_should_call_assertion_passed_for_the_assertion(self):
        assert self.reporter1.calls[3][0] == 'assertion_passed'
    def it_should_pass_the_name_into_assertion_passed(self):
        assert self.reporter1.calls[3][1] == 'method_with_should_in_the_name'

    @assertion
    def it_should_call_context_ended_next(self):
        assert self.reporter1.calls[4][0] == 'context_ended'
    @assertion
    def it_should_pass_in_the_context_name_again(self):
        assert self.reporter1.calls[4][1] == 'TestSpec'
    @assertion
    def it_should_pass_in_no_example_again(self):
        assert self.reporter1.calls[4][2] is NO_EXAMPLE

    def it_should_call_test_run_ended_last(self):
        assert self.reporter1.calls[-1][0] == 'test_run_ended'

    def it_should_do_exactly_the_same_to_the_second_reporter(self):
        assert self.reporter2.calls == self.reporter1.calls
    def it_should_do_exactly_the_same_to_the_third_reporter(self):
        assert self.reporter3.calls == self.reporter1.calls


class WhenAPluginModifiesAnAssertionList:
    def context(self):
        self.ran_reals = False
        class Spec:
            def should1(s):
                self.ran_reals = True
            def should2(s):
                self.ran_reals = True
            def not_an_assertion(s):
                pass
            def __new__(cls):
                cls.instance = super().__new__(cls)
                return cls.instance
        self.spec = Spec

        self.ran_spies = []
        def spy_assertion_method1():
            self.ran_spies.append('spy_assertion_method1')
        def spy_assertion_method2():
            self.ran_spies.append('spy_assertion_method2')

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [spy_assertion_method1, spy_assertion_method2]
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth:{
            Spec.should1: ASSERTION,
            Spec.should2: ASSERTION,
            Spec.not_an_assertion: None
        }[meth]
        self.plugin.process_assertion_list = modify_list

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_pass_a_list_of_the_found_assertions_into_process_assertion_list(self):
        assert isinstance(self.called_with, collections.abc.MutableSequence)
        assert set(self.called_with) == {self.spec.instance.should1, self.spec.instance.should2}

    def it_should_run_the_methods_in_the_list_that_the_plugin_modified(self):
        assert self.ran_spies == ['spy_assertion_method1', 'spy_assertion_method2']

    def it_should_not_run_the_old_version_of_the_list(self):
        assert not self.ran_reals


class WhenAnAssertionFails:
    def context(self):
        self.exception = AssertionError()
        class TestSpec:
            ran_cleanup = False
            def failing_should_method(s):
                raise self.exception
            def second_should_method(s):
                s.__class__.ran_second = True
            def cleanup(s):
                s.__class__.ran_cleanup = True

        self.spec = TestSpec
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter])

    def it_should_call_assertion_failed(self):
        assert "assertion_failed" in [c[0] for c in self.reporter.calls]

    def it_should_pass_in_the_assertion_name(self):
        name = [c for c in self.reporter.calls if c[0] == "assertion_failed"][0][1]
        assert name == "failing_should_method"

    def it_should_pass_in_the_exception(self):
        exception = [c for c in self.reporter.calls if c[0] == "assertion_failed"][0][2]
        assert exception is self.exception

    def it_should_still_run_the_other_assertion(self):
        # not a great test - we can't guarantee that the second should method
        # will get executed after the failing one. If this starts failing it may only fail
        # sometimes.
        assert self.spec.ran_second

    @assertion
    def it_should_still_run_the_cleanup(self):
        assert self.spec.ran_cleanup


class WhenAnAssertionErrors:
    def context(self):
        self.exception = Exception()
        class TestSpec:
            ran_cleanup = False
            def erroring_should_method(s):
                raise self.exception
            def second_should_method(s):
                s.__class__.ran_second = True
            def cleanup(s):
                s.__class__.ran_cleanup = True

        self.spec = TestSpec
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter])

    def it_should_call_assertion_errored(self):
        assert "assertion_errored" in [c[0] for c in self.reporter.calls]

    def it_should_pass_in_the_name(self):
        name = [c for c in self.reporter.calls if c[0] == "assertion_errored"][0][1]
        assert name == "erroring_should_method"

    def it_should_pass_in_the_exception(self):
        exception = [c for c in self.reporter.calls if c[0] == "assertion_errored"][0][2]
        assert exception is self.exception

    def it_should_still_run_the_other_assertion(self):
        # not a great test - we can't guarantee that the second should method
        # will get executed after the failing one. If this starts failing it may only fail
        # sometimes.
        assert self.spec.ran_second

    @assertion
    def it_should_still_run_the_cleanup(self):
        assert self.spec.ran_cleanup


class WhenAContextErrorsDuringTheSetup:
    def context(self):
        self.exception = Exception()
        class ErrorInSetup:
            ran_cleanup = False
            ran_because = False
            ran_assertion = False
            def context(s):
                raise self.exception
            def because(s):
                s.__class__.ran_because = True
            def it(s):
                s.__class__.ran_assertion = True
            def cleanup(s):
                s.__class__.ran_cleanup = True

        self.spec = ErrorInSetup
        self.reporter = SpyReporter()

    def because_we_run_the_specs(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter])

    @assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[2][0] == "context_errored"
    @assertion
    def it_should_pass_in_the_context_name(self):
        assert self.reporter.calls[2][1] == self.spec.__name__
    @assertion
    def it_should_pass_in_no_example(self):
        assert self.reporter.calls[2][2] is NO_EXAMPLE
    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[2][3] is self.exception

    def it_should_not_run_the_action(self):
        assert not self.spec.ran_because
    def it_should_not_run_the_assertion(self):
        assert not self.spec.ran_assertion
    @assertion
    def it_should_still_run_the_cleanup(self):
        assert self.spec.ran_cleanup


class WhenAContextErrorsDuringTheAction:
    def context(self):
        self.exception = Exception()
        class ErrorInAction:
            ran_cleanup = False
            ran_assertion = False
            def because(s):
                raise self.exception
            def it(s):
                s.__class__.ran_assertion = True
            def cleanup(s):
                s.__class__.ran_cleanup = True

        self.spec = ErrorInAction
        self.reporter = SpyReporter()

    def because_we_run_the_specs(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter])

    @assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[2][0] == "context_errored"

    @assertion
    def it_should_pass_in_the_context_name(self):
        assert self.reporter.calls[2][1] == self.spec.__name__

    @assertion
    def it_should_pass_in_no_example(self):
        assert self.reporter.calls[2][2] is NO_EXAMPLE

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[2][3] is self.exception

    def it_should_not_run_the_assertion(self):
        assert not self.spec.ran_assertion

    @assertion
    def it_should_still_run_the_cleanup(self):
        assert self.spec.ran_cleanup


class WhenAContextErrorsDuringTheCleanup:
    def context(self):
        self.exception = Exception()
        class ErrorInTeardown:
            def it(s):
                pass
            def cleanup(s):
                # assertion errors that get raised outside of a
                # 'should' method should be considered context errors
                raise self.exception

        self.spec = ErrorInTeardown
        self.reporter = SpyReporter()

    def because_we_run_the_specs(self):
        run_object(self.spec, [NameBasedIdentifier(), self.reporter])

    @assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[4][0] == "context_errored"

    @assertion
    def it_should_pass_in_the_context_name(self):
        assert self.reporter.calls[4][1] == self.spec.__name__

    @assertion
    def it_should_pass_in_no_example(self):
        assert self.reporter.calls[4][2] is NO_EXAMPLE

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[4][3] is self.exception


class WhenAPluginSetsTheExitCode:
    @classmethod
    def examples_of_exit_codes(cls):
        yield 0
        yield 1
        yield 99

    def context(self, exitcode):
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.get_exit_code.return_value = exitcode

    def because_we_run_something(self):
        self.result = run_object(type('Spec', (), {}), [self.plugin])

    def it_should_return_the_exit_code_from_the_plugin(self, exitcode):
        assert self.result == exitcode


class WhenRunningAClassContainingNoAssertions:
    def context(self):
        class NoAssertions:
            log = []
            def context(self):
                self.__class__.log.append('arrange')
            def because(self):
                self.__class__.log.append('act')
            def cleanup(self):
                self.__class__.log.append('teardown')
        self.spec = NoAssertions

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            NoAssertions.context: SETUP,
            NoAssertions.because: ACTION,
            NoAssertions.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_not_run_the_class(self):
        assert self.spec.log == []


if __name__ == "__main__":
    contexts.main()
