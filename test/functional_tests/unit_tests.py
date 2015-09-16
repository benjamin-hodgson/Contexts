import collections.abc
import types
from unittest import mock
import contexts
from contexts.plugin_interface import PluginInterface, CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN, NO_EXAMPLE
from contexts import assertion
from .tools import UnorderedList, run_object


core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class Mock(mock.Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, unsafe=True, **kwargs)


class WhenAPluginSuppliesAClassToRun:
    def context(self):
        self.ran_method = False

        class TestSpec:
            def method(s):
                self.ran_method = True

        self.spec = TestSpec
        self.plugin = Mock(spec=PluginInterface)
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
                self.log.append(("setup", example))

            def method_two(s, example):
                self.log.append(("action", example))

            def method_three(s, example):
                self.log.append(("assertion", example))

            def method_four(s, example):
                self.log.append(("teardown", example))

        self.spec = TestSpec

        self.none_plugin = Mock(spec=PluginInterface)
        self.none_plugin.identify_method.return_value = None

        self.deleted_plugin = Mock(spec=PluginInterface)
        del self.deleted_plugin.identify_method

        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            TestSpec.method_zero: EXAMPLES,
            TestSpec.method_one: SETUP,
            TestSpec.method_two: ACTION,
            TestSpec.method_three: ASSERTION,
            TestSpec.method_four: TEARDOWN
        }[meth]

        self.too_late_plugin = Mock(spec=PluginInterface)

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
        self.plugin = Mock(spec=PluginInterface)
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
        self.plugin = Mock(spec=PluginInterface)
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

        self.plugin = Mock(spec=PluginInterface)
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

        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = side_effect

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_unexpected_error_with_a_TooManySpecialMethodsError(self):
        assert isinstance(self.plugin.unexpected_error.call_args[0][0], contexts.errors.TooManySpecialMethodsError)

    def it_should_not_run_the_methods(self):
        assert not self.ran_a_method


class WhenRunningASpecWithPlugins:
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

            def __init__(self):
                TestSpec.instance = self

        self.spec = TestSpec

        self.plugin1 = Mock(wraps=PluginInterface())
        del self.plugin1.process_assertion_list
        self.plugin1.identify_method = lambda meth: {
            TestSpec.method_with_establish_in_the_name: SETUP,
            TestSpec.method_with_because_in_the_name: ACTION,
            TestSpec.method_with_should_in_the_name: ASSERTION,
            TestSpec.method_with_cleanup_in_the_name: TEARDOWN
        }[meth]
        self.plugin2 = Mock(wraps=PluginInterface())
        del self.plugin2.process_assertion_list

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin1, self.plugin2])
        self.calls = self.plugin1.mock_calls

    def it_should_call_test_run_started_first(self):
        assert self.calls[0] == mock.call.test_run_started()

    def it_should_call_test_class_started_next(self):
        assert self.calls[1] == mock.call.test_class_started(self.spec)

    @assertion
    def it_should_call_context_started_with_the_name_and_the_example(self):
        assert self.calls[2] == mock.call.context_started(self.spec, NO_EXAMPLE)

    def it_should_call_assertion_started_for_the_assertion(self):
        assert self.calls[3] == mock.call.assertion_started(self.spec.instance.method_with_should_in_the_name)

    def it_should_call_assertion_passed_for_the_assertion(self):
        assert self.calls[4] == mock.call.assertion_passed(self.spec.instance.method_with_should_in_the_name)

    @assertion
    def it_should_call_context_ended_next(self):
        assert self.calls[5] == mock.call.context_ended(self.spec, NO_EXAMPLE)

    def it_should_call_test_class_ended(self):
        assert self.calls[6] == mock.call.test_class_ended(self.spec)

    def finally_it_should_call_test_run_ended(self):
        assert self.calls[7] == mock.call.test_run_ended()

    def it_should_do_exactly_the_same_to_the_other_plugin(self):
        assert self.plugin2.mock_calls == self.calls


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
        self.spec = Spec

        self.ran_spies = []

        def spy_assertion_method1(s):
            self.ran_spies.append('spy_assertion_method1')

        def spy_assertion_method2(s):
            self.ran_spies.append('spy_assertion_method2')

        def modify_list(cls, l):
            self.called_with = (cls, l.copy())
            l[:] = [spy_assertion_method1, spy_assertion_method2]
        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            Spec.should1: ASSERTION,
            Spec.should2: ASSERTION,
            Spec.not_an_assertion: None
        }[meth]
        self.plugin.process_assertion_list = modify_list

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_pass_the_test_class_into_process_assertion_list(self):
        assert self.called_with[0] is self.spec

    def it_should_pass_a_list_of_the_found_assertions_into_process_assertion_list(self):
        assert isinstance(self.called_with[1], collections.abc.MutableSequence)
        assert set(self.called_with[1]) == {self.spec.should1, self.spec.should2}

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

            def __init__(self):
                TestSpec.instance = self

        self.spec = TestSpec
        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_method = lambda meth: {
            TestSpec.failing_should_method: ASSERTION,
            TestSpec.second_should_method: ASSERTION,
            TestSpec.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_assertion_failed_with_the_name_and_the_exception(self):
        self.plugin.assertion_failed.assert_called_once_with(self.spec.instance.failing_should_method, self.exception)

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

            def __init__(self):
                TestSpec.instance = self

        self.spec = TestSpec
        self.plugin = Mock(wraps=PluginInterface())
        self.plugin.identify_method = lambda meth: {
            TestSpec.erroring_should_method: ASSERTION,
            TestSpec.second_should_method: ASSERTION,
            TestSpec.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_call_assertion_errored_with_the_name_and_the_exception(self):
        self.plugin.assertion_errored.assert_called_once_with(self.spec.instance.erroring_should_method, self.exception)

    def it_should_still_run_the_other_assertion(self):
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
        self.plugin = Mock(wraps=PluginInterface())
        self.plugin.identify_method = lambda meth: {
            ErrorInSetup.context: SETUP,
            ErrorInSetup.because: ACTION,
            ErrorInSetup.it: ASSERTION,
            ErrorInSetup.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_specs(self):
        run_object(self.spec, [self.plugin])

    @assertion
    def it_should_call_context_errored_with_the_class_and_no_example_and_the_exception(self):
        self.plugin.context_errored.assert_called_once_with(self.spec, NO_EXAMPLE, self.exception)

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
        self.plugin = Mock(wraps=PluginInterface())
        self.plugin.identify_method = lambda meth: {
            ErrorInAction.because: ACTION,
            ErrorInAction.it: ASSERTION,
            ErrorInAction.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_specs(self):
        run_object(self.spec, [self.plugin])

    @assertion
    def it_should_call_context_errored_with_the_class_and_no_example_and_the_exception(self):
        self.plugin.context_errored.assert_called_once_with(self.spec, NO_EXAMPLE, self.exception)

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
                raise self.exception

        self.spec = ErrorInTeardown
        self.plugin = Mock(wraps=PluginInterface())
        self.plugin.identify_method = lambda meth: {
            ErrorInTeardown.it: ASSERTION,
            ErrorInTeardown.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_specs(self):
        run_object(self.spec, [self.plugin])

    @assertion
    def it_should_call_context_errored_with_the_class_and_no_example_and_the_exception(self):
        self.plugin.context_errored.assert_called_once_with(self.spec, NO_EXAMPLE, self.exception)


class WhenAPluginSetsTheExitCode:
    @classmethod
    def examples_of_exit_codes(cls):
        yield 0
        yield 1
        yield 99

    def context(self, exitcode):
        self.plugin = Mock(spec=PluginInterface)
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

        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_method.side_effect = lambda meth: {
            NoAssertions.context: SETUP,
            NoAssertions.because: ACTION,
            NoAssertions.cleanup: TEARDOWN
        }[meth]

    def because_we_run_the_spec(self):
        run_object(self.spec, [self.plugin])

    def it_should_not_run_the_class(self):
        assert self.spec.log == []


class WhenAPluginChoosesClasses:
    def context(self):
        class ToRun1:
            was_run = False

            def it_should_run_this(self):
                self.__class__.was_run = True

        class ToRun2:
            was_run = False

            def it_should_run_this(self):
                self.__class__.was_run = True

        class NotToRun:
            was_instantiated = False

            def __init__(self):
                self.__class__.was_instantiated = True

        self.module = types.ModuleType('fake_specs')
        self.module.ToRun1 = ToRun1
        self.module.ToRun2 = ToRun2
        self.module.NotToRun = NotToRun

        self.plugin = Mock(spec=PluginInterface)
        self.plugin.identify_class.side_effect = lambda cls: {
            ToRun1: CONTEXT,
            ToRun2: CONTEXT,
            NotToRun: None
        }[cls]
        self.plugin.identify_method.side_effect = lambda meth: {
            ToRun1.it_should_run_this: ASSERTION,
            ToRun2.it_should_run_this: ASSERTION,
        }[meth]
        self.other_plugin = Mock()
        self.other_plugin.identify_class.return_value = None

    def because_we_run_the_module(self):
        run_object(self.module, [self.plugin, self.other_plugin])

    def it_should_run_the_class_the_plugin_likes(self):
        assert self.module.ToRun1.was_run

    def it_should_run_the_other_class_the_plugin_likes(self):
        assert self.module.ToRun2.was_run

    def it_should_only_ask_the_second_plugin_what_to_do_with_the_class_its_not_sure_about(self):
        self.other_plugin.identify_class.assert_called_once_with(self.module.NotToRun)

    def it_should_not_run_the_class_which_neither_plugin_wanted(self):
        assert not self.module.NotToRun.was_instantiated


class WhenAPluginModifiesAClassList:
    def establish_that_a_plugin_is_fiddling_with_the_list(self):
        self.ran_reals = False

        class FoundClass1:
            def it_should_run_this(s):
                self.ran_reals = True

        class FoundClass2:
            def it_should_run_this(s):
                self.ran_reals = True

        self.ran_spies = []

        class AnotherClass1:
            def it_should_run_this(s):
                self.ran_spies.append('AnotherClass1')

        class AnotherClass2:
            def it_should_run_this(s):
                self.ran_spies.append('AnotherClass2')

        self.module = types.ModuleType('fake_specs')
        self.module.FoundClass1 = FoundClass1
        self.module.FoundClass2 = FoundClass2
        self.AnotherClass1 = AnotherClass1
        self.AnotherClass2 = AnotherClass2

        def modify_list(mod, l):
            self.called_with = (mod, l.copy())
            l[:] = [AnotherClass1, AnotherClass2]
        self.plugin = Mock()
        self.plugin.process_class_list = modify_list
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_module(self):
        run_object(self.module, [self.plugin])

    def it_should_pass_the_test_module_into_process_class_list(self):
        assert self.called_with[0] == self.module

    def it_should_pass_a_list_of_the_found_classes_into_process_class_list(self):
        assert isinstance(self.called_with[1], collections.abc.MutableSequence)
        assert set(self.called_with[1]) == {self.module.FoundClass1, self.module.FoundClass2}

    def it_should_run_the_classes_in_the_list_that_the_plugin_modified(self):
        assert self.ran_spies == ['AnotherClass1', 'AnotherClass2']

    def it_should_not_run_the_old_version_of_the_list(self):
        assert not self.ran_reals


if __name__ == "__main__":
    contexts.main()
