import sure
import pyspec


class WhenWeRunASpec(object):
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
            def method_with_cleanup_in_the_name(self):
                self.log += "teardown "

        self.spec = TestSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert teardown ")

    def it_should_report_the_results(self):
        self.result.summary().should.equal("1 assertions, 0 failed")


class WhenWeRunASpecWithMultipleAssertionsWithoutAnEstablishClause(object):
    def establish_the_spec(self):
        class SpecWithoutEstablishOrCleanup(object):
            def __init__(self):
                self.assertions = 0
            def it_should_run_this(self):
                self.assertions += 1
            def it_should_also_run_this(self):
                self.assertions += 1

        self.spec = SpecWithoutEstablishOrCleanup()

    def because_we_run_the_spec(self):
        pyspec.run(self.spec)

    def it_should_still_run_it(self):
        self.spec.assertions.should.equal(2)


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

class WhenASpecFails(object):
    def context(self):
        class FailingSpec(object):
            def it_should_fail(self):
                assert False

        self.spec = FailingSpec()

    def because_we_run_the_spec(self):
        self.result = pyspec.run(self.spec)

    def it_should_report_the_failure(self):
        self.result.summary().should.equal("1 assertions, 1 failed")


if __name__ == "__main__":
    print(pyspec.run(WhenWeRunASpec()).summary())
    print(pyspec.run(WhenASpecFails()).summary())
    print(pyspec.run(WhenWeRunASpecWithMultipleAssertionsWithoutAnEstablishClause()).summary())
    print(pyspec.run(WhenWeRunSpecsWithAlternatelyNamedMethods()).summary())
