import sure
import pyspec


class WhenASpecPasses(object):
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
            def another_method_with_should_in_the_name(self):
                self.log += "assert "
            def method_with_cleanup_in_the_name(self):
                self.log += "teardown "

        self.spec = TestSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert teardown ")

    def it_should_report_the_results(self):
        self.result.summary().should.equal("2 assertions, 0 failed, 0 errors")

class WhenASpecFails(object):
    def context(self):
        class FailingSpec(object):
            def it_should_fail(self):
                assert False

        self.spec = FailingSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_report_the_failure(self):
        self.result.summary().should.equal("1 assertions, 1 failed, 0 errors")

class WhenASpecErrors(object):
    def context(self):
        class ErrorInSetup(object):
            def context(self):
                raise ValueError
            def it(self):
                pass
        class ErrorInAction(object):
            def because(self):
                raise TypeError
            def it(self):
                pass
        class ErrorInAssertion(object):
            def it(self):
                raise TypeError
        class ErrorInTeardown(object):
            def it(self):
                pass
            def cleanup(self):
                raise AttributeError

        self.specs = [ErrorInSetup(), ErrorInAction(), ErrorInAssertion(), ErrorInTeardown()]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            self.results.append(pyspec.run(spec))

    def it_should_report_the_first_failure(self):
        self.results[0].summary().should.equal("1 assertions, 0 failed, 1 errors")
    def it_should_report_the_second_failure(self):
        self.results[1].summary().should.equal("1 assertions, 0 failed, 1 errors")
    def it_should_report_the_third_failure(self):
        self.results[2].summary().should.equal("1 assertions, 0 failed, 1 errors")
    def it_should_report_the_fourth_failure(self):
        self.results[3].summary().should.equal("1 assertions, 0 failed, 1 errors")


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

    def it_should_report_the_results(self):
        self.result.summary().should.equal("2 assertions, 0 failed, 0 errors")

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

    def it_should_report_the_results(self):
        self.result.summary().should.equal("2 assertions, 0 failed, 0 errors")


if __name__ == "__main__":
    specs = [
        WhenASpecPasses(),
        WhenASpecFails(),
        WhenASpecErrors(),
        WhenWeRunSpecsWithAlternatelyNamedMethods(),
        WhenASpecHasASuperclass(),
        WhenRunningMultipleSpecs(),
        WhenRunningMultipleSpecsUsingUnpackedSyntax(),
    ]
    print(pyspec.run(specs).summary())
