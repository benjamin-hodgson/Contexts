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
        pyspec.run(self.spec)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert teardown ")


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
    def establish_the_specs(self):
        class AlternatelyNamedMethods(object):
            def __init__(self):
                self.log = ""
            def context(self):
                self.log += "arrange "
            def has_when_in_the_name(self):  # to prevent collision with Sure
                self.log += "act "
            def it(self):
                self.log += "assert "
        class MoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def since(self):
                self.log += "act "
            def has_must_in_the_name(self):
                self.log += "assert "
        class EvenMoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def after(self):
                self.log += "act "
            def will(self):
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
        self.spec2.log.should.equal("act assert ")
        self.spec3.log.should.equal("act assert ")


if __name__ == "__main__":
    pyspec.run(WhenWeRunASpec())
    pyspec.run(WhenWeRunASpecWithMultipleAssertionsWithoutAnEstablishClause())
    pyspec.run(WhenWeRunSpecsWithAlternatelyNamedMethods())
