import sure
import contexts
from .test_doubles import MockResult

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenRunningASpec(object):
    def context(self):
        self.assertion_err = AssertionError()
        self.value_err = ValueError()

        class TestSpec(object):
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
        self.result = MockResult()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert assert teardown ")

    def it_should_call_suite_started_first(self):
        self.result.calls[0][0].should.equal('suite_started')

    def it_should_call_ctx_started_second(self):
        self.result.calls[1][0].should.equal('context_started')

    def it_should_pass_in_the_ctx(self):
        self.result.calls[1][1].name.should.equal('TestSpec')

    def it_should_call_assertion_started_three_times(self):
        assert self.result.calls[2][0] == "assertion_started"
        self.result.calls[2][0].should.equal('assertion_started')
        self.result.calls[4][0].should.equal('assertion_started')
        self.result.calls[6][0].should.equal('assertion_started')

    def it_should_call_assertion_passed_and_failed_and_errored(self):
        calls = [self.result.calls[i][0] for i in (3,5,7)]
        calls.should.contain('assertion_passed')
        calls.should.contain('assertion_failed')
        calls.should.contain('assertion_errored')

    def the_assertions_should_have_the_right_names(self):
        names = [self.result.calls[i][1].name for i in (3,5,7)]
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name')

    def it_should_pass_in_the_exceptions(self):
        exceptions = {}
        for i in (3,5,7):
            call_name = self.result.calls[i][0]
            if call_name == 'assertion_failed':
                exceptions['fail'] = self.result.calls[i][2]
            if call_name == 'assertion_errored':
                exceptions['error'] = self.result.calls[i][2]

        exceptions['fail'].should.equal(self.assertion_err)
        exceptions['error'].should.equal(self.value_err)

    def it_should_call_ctx_ended_next(self):
        self.result.calls[8][0].should.equal('context_ended')

    def it_should_pass_in_the_ctx_again(self):
        self.result.calls[8][1].should.equal(self.result.calls[1][1])

    def it_should_call_suite_ended_last(self):
        self.result.calls[9][0].should.equal('suite_ended')

    def it_should_pass_in_the_same_suite_as_at_the_start(self):
        self.result.calls[9][1].should.equal(self.result.calls[0][1])

    def it_should_not_make_any_more_calls(self):
        self.result.calls.should.have.length_of(10)

class WhenAContextErrors(object):
    def context(self):
        self.value_err = ValueError("explode")
        self.type_err = TypeError("oh no")
        self.assertion_err = AssertionError("shut up")
        class ErrorInSetup(object):
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
        class ErrorInAction(object):
            ran_cleanup = False
            ran_assertion = False
            def because(s):
                raise self.type_err
            def it(s):
                s.__class__.ran_assertion = True
            def cleanup(s):
                s.__class__.ran_cleanup = True
        class ErrorInTeardown(object):
            def it(s):
                pass
            def cleanup(s):
                # assertion errors that get raised outside of a
                # 'should' method should be considered context errors
                raise self.assertion_err

        self.specs = [ErrorInSetup, ErrorInAction, ErrorInTeardown]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            result = MockResult()
            self.results.append(result)
            contexts.run(spec, result)

    def it_should_call_ctx_errored_for_the_first_error(self):
        self.results[0].calls[2][0].should.equal("context_errored")

    def it_should_pass_in_the_first_exception(self):
        self.results[0].calls[2][2].should.equal(self.value_err)

    def it_should_not_run_the_first_action(self):
        self.specs[0].ran_because.should.be.false

    def it_should_not_run_the_first_assertion(self):
        self.specs[0].ran_assertion.should.be.false

    def it_should_still_run_the_teardown_despite_the_setup_error(self):
        self.specs[0].ran_cleanup.should.be.true

    def it_should_call_ctx_errored_for_the_second_error(self):
        self.results[1].calls[2][0].should.equal("context_errored")

    def it_should_pass_in_the_second_exception(self):
        self.results[1].calls[2][2].should.equal(self.type_err)

    def it_should_not_run_the_second_assertion(self):
        self.specs[1].ran_assertion.should.be.false

    def it_should_still_run_the_teardown_despite_the_action_error(self):
        self.specs[1].ran_cleanup.should.be.true

    def it_should_call_ctx_errored_for_the_third_error(self):
        self.results[2].calls[4][0].should.equal("context_errored")

    def it_should_pass_in_the_third_exception(self):
        self.results[2].calls[4][2].should.equal(self.assertion_err)

class WhenCatchingAnException(object):
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec(object):
            exception = None
            def context(s):
                def throwing_function(a, b, c, d=[]):
                    s.__class__.call_args = (a,b,c,d)
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.__class__.exception = contexts.catch(s.throwing_function, 3, c='yes', b=None)

        self.spec = TestSpec
        self.result = MockResult()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_catch_and_return_the_exception(self):
        self.spec.exception.should.equal(self.exception)

    def it_should_call_it_with_the_supplied_arguments(self):
        self.spec.call_args.should.equal((3, None, 'yes', []))

    def it_should_not_call_failure_methods_on_the_result(self):
        call_names = [call[0] for call in self.result.calls]
        call_names.should_not.contain("context_errored")
        call_names.should_not.contain("assertion_errored")
        call_names.should_not.contain("assertion_failed")

class WhenASpecHasASuperclass(object):
    def context(self):
        self.log = ""
        class SharedContext(object):
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
        self.result = MockResult()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

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

    def it_should_only_call_ctx_started_on_the_result_once(self):
        calls = [call for call in self.result.calls if call[0] == "context_started"]
        calls.should.have.length_of(1)

class WhenASpecHasClassmethods(object):
    def given_a_spec_with_classmethods(self):
        class ClassmethodsSpec(object):
            log = ""
            @classmethod
            def context(cls):
                cls.log += "arrange "
            @classmethod
            def because(cls):
                cls.log += "act "
            @classmethod
            def it(cls):
                cls.log += "assert "
            @classmethod
            def cleanup(cls):
                cls.log += "teardown "
        self.spec = ClassmethodsSpec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, MockResult())

    def it_should_run_the_classmethods(self):
        self.spec.log.should.equal("arrange act assert teardown ")

class WhenASpecHasStaticmethods(object):
    def given_a_spec_with_staticmethods(self):
        self.log = ""
        class StaticmethodsSpec(object):
            @staticmethod
            def context():
                self.log += "arrange "
            @staticmethod
            def because():
                self.log += "act "
            @staticmethod
            def it():
                self.log += "assert "
            @staticmethod
            def cleanup():
                self.log += "teardown "
        self.spec = StaticmethodsSpec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, MockResult())

    def it_should_run_the_staticmethods(self):
        self.log.should.equal("arrange act assert teardown ")

class WhenRunningMultipleSpecs(object):
    def context(self):
        class Spec1(object):
            was_run = False
            def it(self):
                self.__class__.was_run = True
        class Spec2(object):
            was_run = False
            def it(self):
                self.__class__.was_run = True

        self.suite = [Spec1, Spec2]
        self.result = MockResult()

    def because_we_run_the_suite(self):
        contexts.run(self.suite, self.result)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    def it_should_call_ctx_started_twice(self):
        calls = [call for call in self.result.calls if call[0] == "context_started"]
        calls.should.have.length_of(2)

    def it_should_call_ctx_ended_twice(self):
        calls = [call for call in self.result.calls if call[0] == "context_ended"]
        calls.should.have.length_of(2)

class WhenWeRunSpecsWithAlternatelyNamedMethods(object):
    @classmethod
    def examples(self):
        class GivenWhenThen(object):
            log = ""
            def has_given_in_the_name(self):
                self.__class__.log += "arrange "
            def has_when_in_the_name(self):
                self.__class__.log += "act "
            def has_then_in_the_name(self):
                self.__class__.log += "assert "
        yield GivenWhenThen, "arrange act assert "
        class AlternatelyNamedMethods(object):
            log = ""
            @classmethod
            def has_data_in_the_name(cls):
                cls.log += "test_data "
                yield 1
            def has_context_in_the_name(self):
                self.__class__.log += "arrange "
            def has_it_in_the_name(self):
                self.__class__.log += "assert "
        yield AlternatelyNamedMethods, "test_data arrange assert "
        class MoreAlternativeNames(object):
            log = ""
            def has_since_in_the_name(self):
                self.__class__.log += "act "
            def has_must_in_the_name(self):
                self.__class__.log += "assert "
        yield MoreAlternativeNames, "act assert "
        class EvenMoreAlternativeNames(object):
            log = ""
            def has_after_in_the_name(self):
                self.__class__.log += "act "
            def has_will_in_the_name(self):
                self.__class__.log += "assert "
        yield EvenMoreAlternativeNames, "act assert "

    def context(self, example):
        self.spec, self.expected_log = example

    def because_we_run_the_spec(self, example):
        contexts.run(self.spec, MockResult())

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal(self.expected_log)

class WhenRunningAmbiguouslyNamedMethods(object):
    @classmethod
    def examples(cls):
        class AmbiguousMethods1(object):
            def this_has_both_context_and_because_in_the_name(self):
                pass
        class AmbiguousMethods2(object):
            def this_has_both_because_and_should_in_the_name(self):
                pass
        class AmbiguousMethods3(object):
            def this_has_both_should_and_cleanup_in_the_name(self):
                pass
        class AmbiguousMethods4(object):
            def this_has_both_cleanup_and_establish_in_the_name(self):
                pass
        class AmbiguousMethods5(object):
            def this_has_both_examples_and_it_in_the_name(self):
                pass
        yield AmbiguousMethods1
        yield AmbiguousMethods2
        yield AmbiguousMethods3
        yield AmbiguousMethods4
        yield AmbiguousMethods5

    def because_we_try_to_run_the_spec(self, example):
        self.exception = contexts.catch(contexts.run, example, MockResult())

    def it_should_raise_MethodNamingError(self):
        self.exception.should.be.a(contexts.errors.MethodNamingError)

class WhenRunningNotSoAmbiguouslyNamedMethods(object):
    @classmethod
    def examples(self):
        class NotAmbiguousMethods1(object):
            def this_has_both_context_and_establish_in_the_name(self):
                pass
        class NotAmbiguousMethods2(object):
            def this_has_both_because_and_when_in_the_name(self):
                pass
        class NotAmbiguousMethods3(object):
            def this_has_both_should_and_it_in_the_name(self):
                pass
        class NotAmbiguousMethods4(object):
            @classmethod
            def this_has_both_examples_and_data_in_the_name(self):
                yield []
        yield NotAmbiguousMethods1
        yield NotAmbiguousMethods2
        yield NotAmbiguousMethods3
        yield NotAmbiguousMethods4

    def because_we_try_to_run_the_spec(self, example):
        self.exception = contexts.catch(contexts.run, example, MockResult())

    def it_should_not_raise_any_exceptions(self):
        self.exception.should.be.none

class WhenRunningSpecsWithTooManySpecialMethods(object):
    @classmethod
    def examples(cls):
        class TooManyContexts(object):
            def context(self):
                pass
            def establish(self):
                pass
        class TooManyActions(object):
            def because(self):
                pass
            def when(self):
                pass
        class TooManyTeardowns(object):
            def cleanup1(self):
                pass
            def cleanup2(self):
                pass
        class TooManyExamples(object):
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

    def because_we_try_to_run_the_spec(self, example):
        self.exception = contexts.catch(contexts.run, example, MockResult())

    def it_should_raise_TooManySpecialMethodsError(self):
        self.exception.should.be.a(contexts.errors.TooManySpecialMethodsError)


if __name__ == "__main__":
    contexts.main()
