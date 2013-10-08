import types
import sure
import pyspec
from pyspec.reporting import format_result

core_file = repr(pyspec.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenRunningASpec(object):
    def establish_the_spec(self):
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

    def the_result_should_have_one_ctx(self):
        self.result.contexts.should.have.length_of(1)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

    def the_result_should_have_the_failure(self):
        self.result.failures.should.have.length_of(1)

    # TODO: move this
    def it_should_report_the_results(self):
        format_result(self.result).should.match(
"""=+
FAIL: __main__.WhenRunningASpec.establish_the_spec.<locals>.TestSpec.failing_method_with_should_in_the_name
-+
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.func\(\)
  File "{1}", line \d+, in failing_method_with_should_in_the_name
    assert False, "failing assertion"
AssertionError: failing assertion
-+
FAILED!
1 context, 2 assertions: 1 failed, 0 errors
""".format(core_file, this_file))


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

    # TODO: move this
    def it_should_report_the_ctx_error(self):
        format_result(self.results[0]).should.match(
"""=+
ERROR: __main__.WhenASpecErrors.context.<locals>.ErrorInSetup.it
-+
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.run_setup\(\)
  File "{0}", line \d+, in run_setup
    setup\(\)
  File "{1}", line \d+, in context
    raise ValueError\("explode"\)
ValueError: explode
-+
FAILED!
1 context, 1 assertion: 0 failed, 1 error
""".format(core_file, this_file))
    
    # TODO: move this
    def it_should_report_the_action_error(self):
        format_result(self.results[1]).should.match(
"""=+
ERROR: __main__.WhenASpecErrors.context.<locals>.ErrorInAction.it
-+
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.run_action\(\)
  File "{0}", line \d+, in run_action
    action\(\)
  File "{1}", line \d+, in because
    raise TypeError\("oh no"\)
TypeError: oh no
-+
FAILED!
1 context, 1 assertion: 0 failed, 1 error
""".format(core_file, this_file))
    
    # TODO: move this
    def it_should_report_the_assertion_error(self):
        format_result(self.results[2]).should.match(
"""=+
ERROR: __main__.WhenASpecErrors.context.<locals>.ErrorInAssertion.it
-+
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.func\(\)
  File "{1}", line \d+, in it
    1/0
ZeroDivisionError: division by zero
-+
FAILED!
1 context, 1 assertion: 0 failed, 1 error
""".format(core_file, this_file))
    
    # TODO: move this
    def it_should_report_the_trdn_error(self):
        format_result(self.results[3]).should.match(
"""=+
ERROR: __main__.WhenASpecErrors.context.<locals>.ErrorInTeardown.it
-+
Traceback \(most recent call last\):
  File "{0}", line \d+, in run
    self.run_teardown\(\)
  File "{0}", line \d+, in run_teardown
    teardown\(\)
  File "{1}", line \d+, in cleanup
    raise AttributeError\("got it wrong"\)
AttributeError: got it wrong
-+
FAILED!
1 context, 1 assertion: 0 failed, 1 error
""".format(core_file, this_file))

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

    # TODO: move this
    def it_should_report_the_results(self):
        format_result(self.result).should.match("-+\nPASSED!\n2 contexts, 2 assertions\n")

class WhenRunningMultipleSpecsUsingUnpackedSyntax(object):
    def context(self):
        class Spec1(object):
            def it(self):
                self.was_run = True
        class Spec2(object):
            def it(self):
                self.was_run = True

        self.suite = [Spec1(), Spec2()]

    def because_we_run_the_suite(self):
        self.result = pyspec.run(*self.suite)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    # TODO: move this
    def it_should_report_the_results(self):
        format_result(self.result).should.match("-+\nPASSED!\n2 contexts, 2 assertions\n")

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
            was_run = False
            def it_should_not_run_this(self):
                self.__class__.was_run = True
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

    def it_should_not_run_the_normal_class(self):
        self.module.NormalClass.was_run.should.be.false


if __name__ == "__main__":
    pyspec.main()
