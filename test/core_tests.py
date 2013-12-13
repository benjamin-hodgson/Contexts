import sure
import contexts
from .tools import SpyReporter

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


# this test is waaay too big
class WhenRunningASpec:
    def context(self):
        self.assertion_err = AssertionError()
        self.value_err = ValueError()

        class TestSpec:
            log = ""
            def method_with_establish_in_the_name(s):
                s.__class__.log += "arrange "
            def method_with_because_in_the_name(s):
                s.__class__.log += "act "
            def method_with_should_in_the_name(s):
                s.__class__.log += "assert "
            def failing_method_with_should_in_the_name(s):
                s.__class__.log += "assert "
                raise self.assertion_err
            def erroring_method_with_should_in_the_name(s):
                s.__class__.log += "assert "
                raise self.value_err
            def method_with_cleanup_in_the_name(s):
                s.__class__.log += "teardown "

        self.spec = TestSpec
        self.reporter1 = SpyReporter()
        self.reporter2 = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [self.reporter1, self.reporter2])

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert assert teardown ")

    def it_should_call_test_run_started_first(self):
        self.reporter1.calls[0][0].should.equal('test_run_started')

    def it_should_call_suite_started(self):
        self.reporter1.calls[1][0].should.equal('suite_started')

    @contexts.assertion
    def it_should_call_context_started_next(self):
        self.reporter1.calls[2][0].should.equal('context_started')

    @contexts.assertion
    def it_should_pass_in_the_context(self):
        self.reporter1.calls[2][1].name.should.equal('TestSpec')

    def it_should_call_assertion_started_three_times(self):
        self.reporter1.calls[3][0].should.equal('assertion_started')
        self.reporter1.calls[5][0].should.equal('assertion_started')
        self.reporter1.calls[7][0].should.equal('assertion_started')

    def it_should_call_assertion_passed_and_failed_and_errored(self):
        calls = [self.reporter1.calls[i][0] for i in (4,6,8)]
        calls.should.contain('assertion_passed')
        calls.should.contain('assertion_failed')
        calls.should.contain('assertion_errored')

    def the_assertions_should_have_the_right_names(self):
        names = [self.reporter1.calls[i][1].name for i in (4,6,8)]
        names.should.contain('method_with_should_in_the_name')
        names.should.contain('failing_method_with_should_in_the_name')
        names.should.contain('erroring_method_with_should_in_the_name')

    def it_should_pass_in_the_exceptions(self):
        exceptions = {}
        for i in (4,6,8):
            call_name = self.reporter1.calls[i][0]
            if call_name == 'assertion_failed':
                exceptions['fail'] = self.reporter1.calls[i][2]
            if call_name == 'assertion_errored':
                exceptions['error'] = self.reporter1.calls[i][2]

        exceptions['fail'].should.equal(self.assertion_err)
        exceptions['error'].should.equal(self.value_err)

    @contexts.assertion
    def it_should_call_context_ended_next(self):
        self.reporter1.calls[9][0].should.equal('context_ended')

    @contexts.assertion
    def it_should_pass_in_the_context_again(self):
        self.reporter1.calls[9][1].should.equal(self.reporter1.calls[2][1])

    def it_should_call_suite_ended(self):
        self.reporter1.calls[10][0].should.equal('suite_ended')

    def it_should_call_test_run_ended_last(self):
        self.reporter1.calls[11][0].should.equal('test_run_ended')

    def it_should_pass_in_the_same_test_run_as_at_the_start(self):
        self.reporter1.calls[11][1].should.equal(self.reporter1.calls[0][1])

    def it_should_not_make_any_more_calls(self):
        self.reporter1.calls.should.have.length_of(12)

    def it_should_do_exactly_the_same_to_the_second_reporter(self):
        self.reporter2.calls.should.equal(self.reporter1.calls)


# break up this test too
class WhenAContextErrors:
    def context(self):
        self.value_err = ValueError("explode")
        self.type_err = TypeError("oh no")
        self.assertion_err = AssertionError("shut up")
        class ErrorInSetup:
            ran_cleanup = False
            ran_because = False
            ran_assertion = False
            def context(s):
                raise self.value_err
            def because(s):
                s.__class__.ran_because = True
            def it(s):
                s.__class__.ran_assertion = True
            def cleanup(s):
                s.__class__.ran_cleanup = True
        class ErrorInAction:
            ran_cleanup = False
            ran_assertion = False
            def because(s):
                raise self.type_err
            def it(s):
                s.__class__.ran_assertion = True
            def cleanup(s):
                s.__class__.ran_cleanup = True
        class ErrorInTeardown:
            def it(s):
                pass
            def cleanup(s):
                # assertion errors that get raised outside of a
                # 'should' method should be considered context errors
                raise self.assertion_err

        self.specs = [ErrorInSetup, ErrorInAction, ErrorInTeardown]

    def because_we_run_the_specs(self):
        self.reporters = []
        for spec in self.specs:
            reporter = SpyReporter()
            self.reporters.append(reporter)
            contexts.run(spec, [reporter])

    @contexts.assertion
    def it_should_call_context_errored_for_the_first_error(self):
        self.reporters[0].calls[3][0].should.equal("context_errored")

    def it_should_pass_in_the_first_exception(self):
        self.reporters[0].calls[3][2].should.equal(self.value_err)

    def it_should_not_run_the_first_action(self):
        self.specs[0].ran_because.should.be.false

    def it_should_not_run_the_first_assertion(self):
        self.specs[0].ran_assertion.should.be.false

    def it_should_still_run_the_teardown_despite_the_setup_error(self):
        self.specs[0].ran_cleanup.should.be.true

    @contexts.assertion
    def it_should_call_context_errored_for_the_second_error(self):
        self.reporters[1].calls[3][0].should.equal("context_errored")

    def it_should_pass_in_the_second_exception(self):
        self.reporters[1].calls[3][2].should.equal(self.type_err)

    def it_should_not_run_the_second_assertion(self):
        self.specs[1].ran_assertion.should.be.false

    def it_should_still_run_the_teardown_despite_the_action_error(self):
        self.specs[1].ran_cleanup.should.be.true

    @contexts.assertion
    def it_should_call_context_errored_for_the_third_error(self):
        self.reporters[2].calls[5][0].should.equal("context_errored")

    def it_should_pass_in_the_third_exception(self):
        self.reporters[2].calls[5][2].should.equal(self.assertion_err)


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
        first_order.should_not.equal(second_order)

class WhenRunningTheSameClassMultipleTimesWithShuffleDisabled(MultipleRunsSharedContext):
    def because_we_run_the_class_twice_with_shuffle_disabled(self):
        contexts.run(self.spec, [self.reporter1], shuffle=False)
        contexts.run(self.spec, [self.reporter2], shuffle=False)

    def it_should_run_the_assertions_in_the_same_order(self):
        first_order = [call[1].name for call in self.reporter1.calls if call[0] == "assertion_started"]
        second_order = [call[1].name for call in self.reporter2.calls if call[0] == "assertion_started"]
        first_order.should.equal(second_order)


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
        self.log[:19].should.equal("superclass arrange ")

    def it_should_run_the_subclass_setup_next(self):
        self.log[19:36].should.equal("subclass arrange ")

    def it_should_run_the_subclass_action_next(self):
        self.log[36:52].should.equal("subclass action ")

    def it_should_not_run_the_superclass_action(self):
        self.log.should_not.contain("superclass action ")

    def it_should_run_both_assertions(self):
        # We don't care what order the two assertions get run in
        self.log[52:92].should.contain("superclass assertion ")
        self.log[52:92].should.contain("subclass assertion ")

    def it_should_run_the_subclass_teardown_first(self):
        self.log[92:109].should.equal("subclass cleanup ")

    def it_should_run_the_superclass_teardown_second(self):
        self.log[109:238].should.equal("superclass cleanup ")

    @contexts.assertion
    def it_should_only_call_context_started_on_the_reporter_once(self):
        calls = [call for call in self.reporter.calls if call[0] == "context_started"]
        calls.should.have.length_of(1)


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
        self.spec.log.should.equal(expected_log)


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
        self.exception = contexts.catch(contexts.run, example, [self.reporter])

    def it_should_not_throw_an_exception(self):
        self.exception.should.be.none

    def it_should_call_unexpected_error_on_the_reporter(self):
        self.reporter.calls[2][0].should.equal("unexpected_error")

    def it_should_pass_in_a_MethodNamingError(self):
        self.reporter.calls[2][1].should.be.a(contexts.errors.MethodNamingError)

    def it_should_finish_the_test_run(self):
        self.reporter.calls[-1][0].should.equal("test_run_ended")


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
        self.exception.should.be.none


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
        self.exception = contexts.catch(contexts.run, example, [self.reporter])

    def it_should_not_raise_an_exception(self):
        self.exception.should.be.none

    def it_should_call_unexpected_error_on_the_reporter(self):
        self.reporter.calls[2][0].should.equal("unexpected_error")

    def it_should_pass_in_a_TooManySpecialMethodsError(self):
        self.reporter.calls[2][1].should.be.a(contexts.errors.TooManySpecialMethodsError)

    def it_should_finish_the_test_run(self):
        self.reporter.calls[-1][0].should.equal("test_run_ended")


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

    def it_should_not_run_any_assertions(self):
        self.spec.log.should.be.empty

    def it_should_call_test_run_started(self):
        self.reporter.calls[0][0].should.equal('test_run_started')

    def then_it_should_call_test_run_ended(self):
        self.reporter.calls[-1][0].should.equal('test_run_ended')


if __name__ == "__main__":
    contexts.main()
