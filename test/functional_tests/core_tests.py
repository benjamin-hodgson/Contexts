import contexts
from .tools import SpyReporter

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenRunningASpec:
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

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_run_the_methods_in_the_correct_order(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenRunningASpecWithMultipleAssertions:
    def context(self):
        class TestSpec:
            calls = 0
            def method_with_should_in_the_name(self):
                self.__class__.calls += 1
            def another_should_method(self):
                self.__class__.calls += 1
            def third_should_method(self):
                self.__class__.calls += 1

        self.spec = TestSpec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_run_all_three_assertion_methods(self):
        assert self.spec.calls == 3


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
        contexts.run(self.spec, [self.reporter1, self.reporter2, self.reporter3])

    def it_should_call_test_run_started_first(self):
        assert self.reporter1.calls[0][0] == 'test_run_started'

    def it_should_call_suite_started(self):
        assert self.reporter1.calls[1][0] == 'suite_started'

    @contexts.assertion
    def it_should_call_context_started_next(self):
        assert self.reporter1.calls[2][0] == 'context_started'

    @contexts.assertion
    def it_should_pass_in_the_context(self):
        assert self.reporter1.calls[2][1].name == 'TestSpec'

    def it_should_call_assertion_started_for_the_first_assertion(self):
        assert self.reporter1.calls[3][0] == 'assertion_started'

    def it_should_pass_the_first_assertion_into_assertion_started(self):
        assert self.reporter1.calls[3][1].name == 'method_with_should_in_the_name'

    def it_should_call_assertion_passed_for_the_first_assertion(self):
        assert self.reporter1.calls[4][0] == 'assertion_passed'

    def it_should_pass_the_first_assertion_into_assertion_passed(self):
        assert self.reporter1.calls[4][1].name == 'method_with_should_in_the_name'

    @contexts.assertion
    def it_should_call_context_ended_next(self):
        assert self.reporter1.calls[5][0] == 'context_ended'

    @contexts.assertion
    def it_should_pass_in_the_context_again(self):
        assert self.reporter1.calls[5][1] == self.reporter1.calls[2][1]

    def it_should_call_suite_ended(self):
        assert self.reporter1.calls[6][0] == 'suite_ended'

    def it_should_call_test_run_ended_last(self):
        assert self.reporter1.calls[7][0] == 'test_run_ended'

    def it_should_pass_in_the_same_test_run_as_at_the_start(self):
        assert self.reporter1.calls[7][1] == self.reporter1.calls[0][1]

    def it_should_do_exactly_the_same_to_the_second_reporter(self):
        assert self.reporter2.calls == self.reporter1.calls

    def it_should_do_exactly_the_same_to_the_third_reporter(self):
        assert self.reporter3.calls == self.reporter1.calls


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
        contexts.run(self.spec, [self.reporter])

    def it_should_call_assertion_failed(self):
        assert "assertion_failed" in [c[0] for c in self.reporter.calls]

    def it_should_pass_in_the_assertion_object(self):
        assertion = [c for c in self.reporter.calls if c[0] == "assertion_failed"][0][1]
        assert assertion.name == "failing_should_method"

    def it_should_pass_in_the_assertion(self):
        exception = [c for c in self.reporter.calls if c[0] == "assertion_failed"][0][2]
        assert exception is self.exception

    def it_should_still_run_the_other_assertion(self):
        # not a great test - we can't guarantee that the second should method
        # will get executed after the failing one. If this starts failing it may only fail
        # sometimes.
        assert self.spec.ran_second

    @contexts.assertion
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
        contexts.run(self.spec, [self.reporter])

    def it_should_call_assertion_failed(self):
        assert "assertion_errored" in [c[0] for c in self.reporter.calls]

    def it_should_pass_in_the_assertion_object(self):
        assertion = [c for c in self.reporter.calls if c[0] == "assertion_errored"][0][1]
        assert assertion.name == "erroring_should_method"

    def it_should_pass_in_the_assertion(self):
        exception = [c for c in self.reporter.calls if c[0] == "assertion_errored"][0][2]
        assert exception is self.exception

    def it_should_still_run_the_other_assertion(self):
        # not a great test - we can't guarantee that the second should method
        # will get executed after the failing one. If this starts failing it may only fail
        # sometimes.
        assert self.spec.ran_second

    @contexts.assertion
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
        contexts.run(self.spec, [self.reporter])

    @contexts.assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[3][0] == "context_errored"

    @contexts.assertion
    def it_should_pass_in_the_context(self):
        assert self.reporter.calls[3][1].name == self.spec.__name__

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[3][2] is self.exception

    def it_should_not_run_the_action(self):
        assert not self.spec.ran_because

    def it_should_not_run_the_assertion(self):
        assert not self.spec.ran_assertion

    @contexts.assertion
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
        contexts.run(self.spec, [self.reporter])

    @contexts.assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[3][0] == "context_errored"

    @contexts.assertion
    def it_should_pass_in_the_context(self):
        assert self.reporter.calls[3][1].name == self.spec.__name__

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[3][2] is self.exception

    def it_should_not_run_the_assertion(self):
        assert not self.spec.ran_assertion

    @contexts.assertion
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
        contexts.run(self.spec, [self.reporter])

    @contexts.assertion
    def it_should_call_context_errored(self):
        assert self.reporter.calls[5][0] == "context_errored"

    @contexts.assertion
    def it_should_pass_in_the_context(self):
        assert self.reporter.calls[5][1].name == self.spec.__name__

    def it_should_pass_in_the_exception(self):
        assert self.reporter.calls[5][2] is self.exception


class MultipleRunsSharedContext:
    def context(self):
        self.create_class()

        self.reporter1 = SpyReporter()
        self.reporter2 = SpyReporter()
    def create_class(self):
        cls_dict = {}
        for x in range(100):
            method_name = 'it' + str(x)
            def it(self):
                pass
            it.__name__ = method_name
            cls_dict[method_name] = it
        self.spec = type("Spec", (object,), cls_dict)

class WhenRunningTheSameClassMultipleTimes(MultipleRunsSharedContext):
    def because_we_run_the_class_twice(self):
        contexts.run(self.spec, [self.reporter1])
        contexts.run(self.spec, [self.reporter2])

    def it_should_run_the_assertions_in_a_different_order(self):
        first_order = [call[1].name for call in self.reporter1.calls if call[0] == "assertion_started"]
        second_order = [call[1].name for call in self.reporter2.calls if call[0] == "assertion_started"]
        assert first_order != second_order

class WhenRunningTheSameClassMultipleTimesWithShuffleDisabled(MultipleRunsSharedContext):
    def because_we_run_the_class_twice_with_shuffle_disabled(self):
        contexts.run(self.spec, [self.reporter1], shuffle=False)
        contexts.run(self.spec, [self.reporter2], shuffle=False)

    def it_should_run_the_assertions_in_the_same_order(self):
        first_order = [call[1].name for call in self.reporter1.calls if call[0] == "assertion_started"]
        second_order = [call[1].name for call in self.reporter2.calls if call[0] == "assertion_started"]
        assert first_order == second_order


class WhenASpecHasASuperclass:
    def context(self):
        self.log = ""
        class SharedContext:
            def context(s):
                self.log += "superclass arrange "
            def superclass_because(s):
                self.log += "superclass action "
            def it(s):
                self.log += "superclass assertion "
            def cleanup(s):
                self.log += "superclass cleanup "
        class Spec(SharedContext):
            # I want it to run the superclasses' specially-named methods
            # _even if_ they are masked by the subclass
            def context(s):
                self.log += "subclass arrange "
            def because(s):
                self.log += "subclass action "
            def it(s):
                self.log += "subclass assertion "
            def cleanup(s):
                self.log += "subclass cleanup "

        self.spec = Spec
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [self.reporter])

    def it_should_run_the_superclass_setup_first(self):
        assert self.log[:19] == "superclass arrange "

    def it_should_run_the_subclass_setup_next(self):
        assert self.log[19:36] == "subclass arrange "

    def it_should_run_the_subclass_action_next(self):
        assert self.log[36:52] == "subclass action "

    def it_should_not_run_the_superclass_action(self):
        assert "superclass action " not in self.log

    def it_should_run_both_assertions(self):
        # We don't care what order the two assertions get run in
        assert "superclass assertion " in self.log[52:92]
        assert "subclass assertion " in self.log[52:92]

    def it_should_run_the_subclass_teardown_first(self):
        assert self.log[92:109] == "subclass cleanup "

    def it_should_run_the_superclass_teardown_second(self):
        assert self.log[109:238] == "superclass cleanup "

    @contexts.assertion
    def it_should_only_call_context_started_on_the_reporter_once(self):
        assert len([call for call in self.reporter.calls if call[0] == "context_started"]) == 1


class WhenWeRunSpecsWithAlternatelyNamedMethods:
    @classmethod
    def examples(self):
        class GivenWhenThen:
            log = ""
            def has_given_in_the_name(self):
                self.__class__.log += "arrange "
            def has_when_in_the_name(self):
                self.__class__.log += "act "
            def has_then_in_the_name(self):
                self.__class__.log += "assert "
        class AlternatelyNamedMethods:
            log = ""
            @classmethod
            def has_data_in_the_name(cls):
                cls.log += "test_data "
                yield 1
            def has_context_in_the_name(self):
                self.__class__.log += "arrange "
            def has_it_in_the_name(self):
                self.__class__.log += "assert "
        class MoreAlternativeNames:
            log = ""
            def has_since_in_the_name(self):
                self.__class__.log += "act "
            def has_must_in_the_name(self):
                self.__class__.log += "assert "
        class EvenMoreAlternativeNames:
            log = ""
            def has_after_in_the_name(self):
                self.__class__.log += "act "
            def has_will_in_the_name(self):
                self.__class__.log += "assert "
        yield GivenWhenThen, "arrange act assert "
        yield AlternatelyNamedMethods, "test_data arrange assert "
        yield MoreAlternativeNames, "act assert "
        yield EvenMoreAlternativeNames, "act assert "

    def context(self, spec, _):
        self.spec = spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_run_the_methods_in_the_correct_order(self, _, expected_log):
        assert self.spec.log == expected_log


class WhenRunningAmbiguouslyNamedMethods:
    @classmethod
    def examples(cls):
        class AmbiguousMethods1:
            def this_has_both_context_and_because_in_the_name(self):
                pass
        class AmbiguousMethods2:
            def this_has_both_because_and_should_in_the_name(self):
                pass
        class AmbiguousMethods3:
            def this_has_both_should_and_cleanup_in_the_name(self):
                pass
        class AmbiguousMethods4:
            def this_has_both_cleanup_and_establish_in_the_name(self):
                pass
        class AmbiguousMethods5:
            @classmethod
            def this_has_both_examples_and_it_in_the_name(self):
                pass
        yield AmbiguousMethods1
        yield AmbiguousMethods2
        yield AmbiguousMethods3
        yield AmbiguousMethods4
        yield AmbiguousMethods5

    def context(self):
        self.reporter = SpyReporter()

    def because_we_try_to_run_the_spec(self, example):
        contexts.run(example, [self.reporter])

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.reporter.calls[2][0] == "unexpected_error"

    def it_should_pass_in_a_MethodNamingError(self):
        assert isinstance(self.reporter.calls[2][1], contexts.errors.MethodNamingError)

    def it_should_finish_the_test_run(self):
        assert self.reporter.calls[-1][0] == "test_run_ended"


class WhenRunningNotSoAmbiguouslyNamedMethods:
    @classmethod
    def examples(self):
        class NotAmbiguousMethods1:
            def this_has_both_context_and_establish_in_the_name(self):
                pass
        class NotAmbiguousMethods2:
            def this_has_both_because_and_when_in_the_name(self):
                pass
        class NotAmbiguousMethods3:
            def this_has_both_should_and_it_in_the_name(self):
                pass
        class NotAmbiguousMethods4:
            @classmethod
            def this_has_both_examples_and_data_in_the_name(self):
                yield 1
        yield NotAmbiguousMethods1
        yield NotAmbiguousMethods2
        yield NotAmbiguousMethods3
        yield NotAmbiguousMethods4

    def because_we_try_to_run_the_spec(self, example):
        self.exception = contexts.catch(contexts.run, example, [])

    def it_should_not_raise_any_exceptions(self):
        assert self.exception is None


class WhenRunningSpecsWithTooManySpecialMethods:
    @classmethod
    def examples(cls):
        class TooManyContexts:
            def context(self):
                pass
            def establish(self):
                pass
        class TooManyActions:
            def because(self):
                pass
            def when(self):
                pass
        class TooManyTeardowns:
            def cleanup1(self):
                pass
            def cleanup2(self):
                pass
        class TooManyExamples:
            @classmethod
            def examples(self):
                pass
            @classmethod
            def test_data(self):
                pass
        yield TooManyContexts
        yield TooManyActions
        yield TooManyTeardowns
        yield TooManyExamples

    def context(self):
        self.reporter = SpyReporter()

    def because_we_try_to_run_the_spec(self, example):
        contexts.run(example, [self.reporter])

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.reporter.calls[2][0] == "unexpected_error"

    def it_should_pass_in_a_TooManySpecialMethodsError(self):
        assert isinstance(self.reporter.calls[2][1], contexts.errors.TooManySpecialMethodsError)

    def it_should_finish_the_test_run(self):
        assert self.reporter.calls[-1][0] == "test_run_ended"


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
        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [self.reporter])

    def it_should_not_run_the_class(self):
        assert self.spec.log == []


if __name__ == "__main__":
    contexts.main()
