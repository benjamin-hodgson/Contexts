import types
import sure
import pyspec
from pyspec import core
from pyspec.reporting import format_result

core_file = repr(pyspec.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]

class WhenRunningASpec(object):
    def context(self):
        class TestSpec(object):
            def __init__(self):
                self.log = ""
            def method_with_establish_in_the_name(self):
                self.log += "arrange "
            def method_with_because_in_the_name(self):
                self.log += "act "
            def method_with_should_in_the_name(self):
                self.log += "assert "
            def failing_method_with_should_in_the_name(self):
                self.log += "assert "
                assert False, "failing assertion"
            def method_with_cleanup_in_the_name(self):
                self.log += "teardown "

        self.spec = TestSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert teardown ")

    # Do we want to assert that the context/assertions point to the right class/method?
    # Runs the risk of coupling the test code to the implementation of Context, Assertion and so on.
    def the_result_should_have_one_ctx(self):
        self.result.contexts.should.have.length_of(1)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

    def the_result_should_have_the_failure(self):
        self.result.failures.should.have.length_of(1)

class WhenASpecErrors(object):
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
        class ErrorInAssertion(object):
            def it(self):
                1/0
        class ErrorInTeardown(object):
            def it(self):
                pass
            def cleanup(self):
                raise AttributeError("got it wrong")

        self.specs = [ErrorInSetup(), ErrorInAction(), ErrorInAssertion(), ErrorInTeardown()]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            self.results.append(pyspec.run(spec))

    def the_result_should_contain_the_ctx_error(self):
        self.results[0].errors.should.have.length_of(1)

    def the_result_should_contain_the_action_error(self):
        self.results[1].errors.should.have.length_of(1)

    def the_result_should_contain_the_assertion_error(self):
        self.results[2].errors.should.have.length_of(1)

    def the_result_should_contain_the_trdn_error(self):
        self.results[3].errors.should.have.length_of(1)

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
            def has_after_in_the_name(self):
                self.log += "act "
            def has_will_in_the_name(self):
                self.log += "assert "

        self.spec1 = AlternatelyNamedMethods()
        self.spec2 = MoreAlternativeNames()
        self.spec3 = EvenMoreAlternativeNames()

    def because_we_run_the_specs(self):
        pyspec.run(self.spec1)
        pyspec.run(self.spec2)
        pyspec.run(self.spec3)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec1.log.should.equal("arrange act assert ")
        self.spec2.log.should.equal("arrange act assert cleanup ")
        self.spec3.log.should.equal("act assert ")

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
            self.exceptions.append(pyspec.catch(lambda: pyspec.run(spec)))

    def it_should_raise_MethodNamingError(self):
        self.exceptions[0].should.be.a(pyspec.errors.MethodNamingError)
        self.exceptions[1].should.be.a(pyspec.errors.MethodNamingError)
        self.exceptions[2].should.be.a(pyspec.errors.MethodNamingError)
        self.exceptions[3].should.be.a(pyspec.errors.MethodNamingError)

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
            self.exceptions.append(pyspec.catch(lambda: pyspec.run(spec)))

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
            self.exceptions.append(pyspec.catch(lambda: pyspec.run(spec)))

    def it_should_raise_TooManySpecialMethodsError(self):
        self.exceptions[0].should.be.a(pyspec.errors.TooManySpecialMethodsError)
        self.exceptions[1].should.be.a(pyspec.errors.TooManySpecialMethodsError)
        self.exceptions[2].should.be.a(pyspec.errors.TooManySpecialMethodsError)

class WhenDeliberatelyCatchingAnException(object):
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec(object):
            def __init__(s):
                s.exception = None
            def context(s):
                def throwing_function():
                    # Looks weird! Referencing 'self' from outer scope
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.exception = pyspec.catch(s.throwing_function)

        self.spec = TestSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_catch_and_return_the_exception(self):
        self.spec.exception.should.equal(self.exception)

    def it_should_not_have_a_failure_result(self):
        self.result.assertions.should.have.length_of(1)
        self.result.failures.should.be.empty
        self.result.errors.should.be.empty

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
        pyspec.run(self.spec)

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

    def because_we_run_the_suite(self):
        self.result = pyspec.run(self.suite)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    def the_result_should_have_two_ctxs(self):
        self.result.contexts.should.have.length_of(2)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

class WhenLoadingTestsFromAModule(object):
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
        self.result = pyspec.run(self.module)

    def it_should_run_the_spec(self):
        self.module.Spec.was_run.should.be.true

    def it_should_run_the_other_spec(self):
        self.module.When.was_run.should.be.true

    def it_should_not_instantiate_the_normal_class(self):
        self.module.NormalClass.was_instantiated.should.be.false

class WhenFormattingASuccessfulResult(object):
    def context_of_successful_run(self):
        assertion1 = core.Assertion(lambda: 2)
        assertion1.ran = True
        assertion2 = core.Assertion(lambda: 2)
        assertion2.ran = True
        assertion3 = core.Assertion(lambda: 2)
        assertion3.ran = True
        ctx1 = core.Context([],[],[assertion1],[])
        ctx2 = core.Context([],[],[assertion2, assertion3],[])
        self.result = core.Result([ctx1, ctx2])

    def because_we_format_the_result(self):
        self.output_string = format_result(self.result)

    def it_should_output_a_summary(self):
        self.output_string.should.equal(
"""----------------------------------------------------------------------
PASSED!
2 contexts, 3 assertions
""")

class WhenFormattingAFailureResult(object):
    def context_of_failed_run(self):
        class TestSpec(object):
            # It'd be nice if I could get away with not throwing real exceptions
            # in this test code.
            # I'd prefer to set up a fake Result object with some assertions and
            # a fake traceback. That way it'd be easier to control the content of
            # the output, and our test of the reporting code would be totally
            # detached from the behaviour of the runner.
            # Unfortunately, looks like you can't really fake traceback objects: see
            # http://stackoverflow.com/a/9193252/1523776
            def this_should_pass(self):
                assert True
            def this_should_fail(self):
                assert False, "failing assertion"
            def this_should_also_fail(self):
                raise AttributeError("Gotcha")
        self.result = pyspec.run(TestSpec())

    def because_we_format_the_result(self):
        self.output_string = format_result(self.result)

    def it_should_output_a_traceback_for_each_failure(self):
        self.output_string.should.match(
# We don't know which way around the assertions will be reported;
# nor do we know the exact file or line number.
# (if we had full control over the Result in this case, this wouldn't be an issue)
r"""(======================================================================
ERROR: __main__.WhenFormattingAFailureResult.context_of_failed_run.<locals>.TestSpec.this_should_also_fail
----------------------------------------------------------------------
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.func\(\)
  File "{1}", line \d+, in this_should_also_fail
    raise AttributeError\("Gotcha"\)
AttributeError: Gotcha
|======================================================================
FAIL: __main__.WhenFormattingAFailureResult.context_of_failed_run.<locals>.TestSpec.this_should_fail
----------------------------------------------------------------------
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.func\(\)
  File "{1}", line \d+, in this_should_fail
    assert False, "failing assertion"
AssertionError: failing assertion
){{2}}----------------------------------------------------------------------
FAILED!
1 context, 3 assertions: 1 failed, 1 error
""".format(core_file, this_file))

if __name__ == "__main__":
    pyspec.main()
