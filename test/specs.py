import types
from io import StringIO
import sure
import contexts
from contexts import reporting

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenRunningASpec(object):
    def context(self):
        self.assertion_err = AssertionError()
        self.value_err = ValueError()

        class TestSpec(object):
            def __init__(s):
                s.log = ""
            def method_with_establish_in_the_name(s):
                s.log += "arrange "
            def method_with_because_in_the_name(s):
                s.log += "act "
            def method_with_should_in_the_name(s):
                s.log += "assert "
            def failing_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.assertion_err
            def erroring_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.value_err
            def method_with_cleanup_in_the_name(s):
                s.log += "teardown "

        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert assert teardown ")

    def the_result_should_report_failure(self):
        self.result.failed.should.be.true

    def the_result_should_have_one_ctx(self):
        self.result.contexts.should.have.length_of(1)

    def the_ctx_should_have_the_right_name(self):
        self.result.contexts[0].name.should.equal("TestSpec")

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(3)

    def the_assertions_should_have_the_right_names(self):
        names = [a.name for a in self.result.assertions]
        names.should.contain('__main__.WhenRunningASpec.context.<locals>.TestSpec.method_with_should_in_the_name')
        names.should.contain('__main__.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name')
        names.should.contain('__main__.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name')

    def the_result_should_have_one_failure(self):
        self.result.assertion_failures.should.have.length_of(1)

    def the_failure_should_have_the_right_name(self):
        self.result.assertion_failures[0][0].name.should.equal(
            '__main__.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name'
        )

    def the_failure_should_have_the_exception(self):
        self.result.assertion_failures[0][1].should.equal(self.assertion_err)

    def the_failure_should_have_the_traceback(self):
        self.result.assertion_failures[0][2].should_not.be.empty

    def the_result_should_have_one_error(self):
        self.result.assertion_errors.should.have.length_of(1)

    def the_error_should_have_the_right_name(self):
        self.result.assertion_errors[0][0].name.should.equal(
            '__main__.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name'
        )

    def the_error_should_have_the_exception(self):
        self.result.assertion_errors[0][1].should.equal(self.value_err)

    def the_error_should_have_the_traceback(self):
        self.result.assertion_errors[0][2].should_not.be.empty

class WhenASpecPasses(object):
    def context(self):
        class TestSpec(object):
            def it(self):
                pass
        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def the_result_should_report_success(self):
        self.result.failed.should.be.false

class WhenAContextErrors(object):
    def context(self):
        class ErrorInSetup(object):
            def context(self):
                raise ValueError("explode")
            def it(self):
                pass
        class ErrorInAction(object):
            def because(self):
                raise TypeError("oh no")
            def it(self):
                pass
        class ErrorInTeardown(object):
            def it(self):
                pass
            def cleanup(self):
                raise AttributeError("got it wrong")

        self.specs = [ErrorInSetup(), ErrorInAction(), ErrorInTeardown()]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            result = contexts.core.Result()
            self.results.append(result)
            contexts.run(spec, result)

    def the_result_should_contain_the_ctx_error(self):
        self.results[0].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_action_error(self):
        self.results[1].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_trdn_error(self):
        self.results[2].context_errors.should.have.length_of(1)

class WhenWeRunSpecsWithAlternatelyNamedMethods(object):
    def context(self):
        class AlternatelyNamedMethods(object):
            def __init__(self):
                self.log = ""
            def has_context_in_the_name(self):
                self.log += "arrange "
            def has_when_in_the_name(self):
                self.log += "act "
            def has_it_in_the_name(self):
                self.log += "assert "
        class MoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_setup_in_the_name(self):
                self.log += "arrange "
            def has_since_in_the_name(self):
                self.log += "act "
            def has_must_in_the_name(self):
                self.log += "assert "
            def has_teardown_in_the_name(self):
                self.log += "cleanup "
        class EvenMoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_given_in_the_name(self):
                self.log += "arrange "
            def has_after_in_the_name(self):
                self.log += "act "
            def has_will_in_the_name(self):
                self.log += "assert "

        self.spec1 = AlternatelyNamedMethods()
        self.spec2 = MoreAlternativeNames()
        self.spec3 = EvenMoreAlternativeNames()

    def because_we_run_the_specs(self):
        contexts.run(self.spec1, contexts.core.Result())
        contexts.run(self.spec2, contexts.core.Result())
        contexts.run(self.spec3, contexts.core.Result())

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec1.log.should.equal("arrange act assert ")
        self.spec2.log.should.equal("arrange act assert cleanup ")
        self.spec3.log.should.equal("arrange act assert ")

class WhenRunningAmbiguouslyNamedMethods(object):
    def context(self):
        class AmbiguousMethods1(object):
            def this_has_both_context_and_because_in_the_name(self):
                pass
        class AmbiguousMethods2(object):
            def this_has_both_because_and_should_in_the_name(self):
                pass
        class AmbiguousMethods3(object):
            def this_has_both_should_and_teardown_in_the_name(self):
                pass
        class AmbiguousMethods4(object):
            def this_has_both_teardown_and_establish_in_the_name(self):
                pass

        self.specs = [AmbiguousMethods1(), AmbiguousMethods2(), AmbiguousMethods3(), AmbiguousMethods4()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_raise_MethodNamingError(self):
        self.exceptions[0].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[1].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[2].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[3].should.be.a(contexts.errors.MethodNamingError)

class WhenRunningNotSoAmbiguouslyNamedMethods(object):
    def context(self):
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
            def this_has_both_teardown_and_cleanup_in_the_name(self):
                pass

        self.specs = [NotAmbiguousMethods1(), NotAmbiguousMethods2(), NotAmbiguousMethods3(), NotAmbiguousMethods4()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_not_raise_any_exceptions(self):
        self.exceptions[0].should.be.none
        self.exceptions[1].should.be.none
        self.exceptions[2].should.be.none
        self.exceptions[3].should.be.none

class WhenRunningSpecsWithTooManySpecialMethods(object):
    def context(self):
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
            def cleanup(self):
                pass
            def teardown(self):
                pass

        self.specs = [TooManyContexts(), TooManyActions(), TooManyTeardowns()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_raise_TooManySpecialMethodsError(self):
        self.exceptions[0].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[1].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[2].should.be.a(contexts.errors.TooManySpecialMethodsError)

class WhenCatchingAnException(object):
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec(object):
            def __init__(s):
                s.exception = None
            def context(s):
                def throwing_function(a, b, c, d=[]):
                    s.call_args = (a,b,c,d)
                    # Looks weird! Referencing 'self' from outer scope
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.exception = contexts.catch(s.throwing_function, 3, c='yes', b=None)

        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_catch_and_return_the_exception(self):
        self.spec.exception.should.equal(self.exception)

    def it_should_call_it_with_the_supplied_arguments(self):
        self.spec.call_args.should.equal((3, None, 'yes', []))

    def it_should_not_have_a_failure_result(self):
        self.result.assertions.should.have.length_of(1)
        self.result.assertion_failures.should.be.empty
        self.result.context_errors.should.be.empty
        self.result.assertion_errors.should.be.empty

class WhenASpecHasASuperclass(object):
    def context(self):
        class SharedContext(object):
            def __init__(self):
                self.log = ""
            def context(self):
                self.log += "superclass arrange "
            def superclass_because(self):
                self.log += "superclass action "
            def it(self):
                self.log += "superclass assertion "
            def cleanup(self):
                self.log += "superclass cleanup "
        class Spec(SharedContext):
            # I want it to run the superclasses' specially-named methods
            # _even if_ they are masked by the subclass
            def context(self):
                self.log += "subclass arrange "
            def because(self):
                self.log += "subclass action "
            def it(self):
                self.log += "subclass assertion "
            def cleanup(self):
                self.log += "subclass cleanup "

        self.spec = Spec()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, contexts.core.Result())

    def it_should_run_the_superclass_ctx_first(self):
        self.spec.log[:19].should.equal("superclass arrange ")

    def it_should_run_the_subclass_ctx_next(self):
        self.spec.log[19:36].should.equal("subclass arrange ")

    def it_should_run_the_subclass_bec_next(self):
        self.spec.log[36:52].should.equal("subclass action ")

    def it_should_not_run_the_superclass_bec(self):
        self.spec.log.should_not.contain("superclass action ")

    def it_should_run_both_assertions(self):
        # We don't care what order the two assertions get run in
        self.spec.log[52:92].should.contain("superclass assertion ")
        self.spec.log[52:92].should.contain("subclass assertion ")

    def it_should_run_the_subclass_clean_first(self):
        self.spec.log[92:109].should.equal("subclass cleanup ")

    def it_should_run_the_superclass_clean_second(self):
        self.spec.log[109:238].should.equal("superclass cleanup ")

class WhenRunningMultipleSpecs(object):
    def context(self):
        class Spec1(object):
            def it(self):
                self.was_run = True
        class Spec2(object):
            def it(self):
                self.was_run = True

        self.suite = [Spec1(), Spec2()]
        self.result = contexts.core.Result()

    def because_we_run_the_suite(self):
        contexts.run(self.suite, self.result)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    def the_result_should_have_two_ctxs(self):
        self.result.contexts.should.have.length_of(2)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

class WhenRunningAClass(object):
    def context(self):
        class TestSpec(object):
            was_run = False
            def it(self):
                self.__class__.was_run = True
        self.spec = TestSpec

    def because_we_run_the_class(self):
        contexts.run(self.spec, contexts.core.Result())

    def it_should_run_the_test(self):
        self.spec.was_run.should.be.true

class WhenRunningAModule(object):
    def context(self):
        class Spec(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class When(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class NormalClass(object):
            was_instantiated = False
            def __init__(self):
                self.__class__.was_instantiated = True
        self.module = types.ModuleType('fake_specs')
        self.module.Spec = Spec
        self.module.When = When
        self.module.NormalClass = NormalClass

    def because_we_run_the_module(self):
        contexts.run(self.module, contexts.core.Result())

    def it_should_run_the_spec(self):
        self.module.Spec.was_run.should.be.true

    def it_should_run_the_other_spec(self):
        self.module.When.was_run.should.be.true

    def it_should_not_instantiate_the_normal_class(self):
        self.module.NormalClass.was_instantiated.should.be.false


#####################################################################
# Reporting tests (will be in separate file later)
#####################################################################

class WhenWatchingForDots(object):
    def context(self):
        self.stringio = StringIO()
        self.result = reporting.TextResult(self.stringio)

    def because_we_run_some_assertions(self):
        with self.result.run_context(None):
            with self.result.run_assertion(None):
                pass
            self.first = self.stringio.getvalue()
            with self.result.run_assertion(None):
                pass
            self.second = self.stringio.getvalue()
            with self.result.run_assertion(None):
                raise AssertionError()
            self.third = self.stringio.getvalue()
            with self.result.run_assertion(None):
                raise TypeError()
            self.fourth = self.stringio.getvalue()
            raise ValueError()
        self.fifth = self.stringio.getvalue()

    def it_should_print_a_dot_for_the_first_pass(self):
        self.first.should.equal('.')

    def it_should_print_a_dot_for_the_second_pass(self):
        self.second.should.equal('..')

    def it_should_print_an_F_for_the_failure(self):
        self.third.should.equal('..F')

    def it_should_print_an_E_for_the_assertion_error(self):
        self.fourth.should.equal('..FE')

    def it_should_print_an_E_for_the_ctx_error(self):
        self.fifth.should.equal('..FEE')

class WhenPrintingASuccessfulResult(object):
    def in_the_context_of_a_successful_run(self):
        # We don't want it to try and print anything while we set it up
        self.result = reporting.TextResult(StringIO())
        with self.result.run_context(None):
            with self.result.run_assertion(None):
                pass
            with self.result.run_assertion(None):
                pass
        with self.result.run_context(None):
            with self.result.run_assertion(None):
                pass

        self.stringio = StringIO()
        self.result.stream = self.stringio

    def because_we_print_the_summary(self):
        self.result.print_summary()

    def it_should_print_the_summary_to_the_stream(self):
        self.stringio.getvalue().should.equal(
"""
----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")

class WhenPrintingAFailureResult(object):
    def in_the_context_of_a_failed_run(self):
        self.result = reporting.TextResult(StringIO())

        exception1 = TypeError("Gotcha")
        tb1 = [('made_up_file.py', 3, 'made_up_function', 'frame1'),
               ('another_made_up_file.py', 2, 'another_made_up_function', 'frame2')]
        assertion1 = contexts.core.Assertion(None, "made.up.assertion_1")

        exception2 = AssertionError("you fail")
        tb2 = [('made_up_file_3.py', 1, 'made_up_function_3', 'frame3'),
               ('made_up_file_4.py', 2, 'made_up_function_4', 'frame4')]
        assertion2 = contexts.core.Assertion(None, "made.up.assertion_2")

        exception3 = ZeroDivisionError("oh dear")
        tb3 = [('made_up_file_4.py', 1, 'made_up_function_4', 'frame4'),
               ('made_up_file_5.py', 2, 'made_up_function_5', 'frame5')]
        context3 = contexts.core.Context([],[],[],[],"made.up_context")

        with self.result.run_context(None):
            # Figure out a way to do this using the context manager?
            self.result.assertion_errored(assertion1, exception1, tb1)
            self.result.assertion_failed(assertion2, exception2, tb2)

        self.result.context_errored(context3, exception3, tb3)

        self.stringio = StringIO()
        self.result.stream = self.stringio

    def because_we_print_the_summary(self):
        self.result.print_summary()

    def it_should_print_a_traceback_for_each_failure(self):
        self.stringio.getvalue().should.equal(
"""
======================================================================
ERROR: made.up_context
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file_4.py", line 1, in made_up_function_4
    frame4
  File "made_up_file_5.py", line 2, in made_up_function_5
    frame5
ZeroDivisionError: oh dear
======================================================================
ERROR: made.up.assertion_1
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file.py", line 3, in made_up_function
    frame1
  File "another_made_up_file.py", line 2, in another_made_up_function
    frame2
TypeError: Gotcha
======================================================================
FAIL: made.up.assertion_2
----------------------------------------------------------------------
Traceback (most recent call last):
  File "made_up_file_3.py", line 1, in made_up_function_3
    frame3
  File "made_up_file_4.py", line 2, in made_up_function_4
    frame4
AssertionError: you fail
----------------------------------------------------------------------
FAILED!
2 contexts, 2 assertions: 1 failed, 2 errors
""")

if __name__ == "__main__":
    contexts.main()
