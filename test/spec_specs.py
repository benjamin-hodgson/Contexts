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
            def it_should_run_these_after_setup(self):
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


if __name__ == "__main__":
    pyspec.run(WhenWeRunASpec())
    pyspec.run(WhenWeRunASpecWithMultipleAssertionsWithoutAnEstablishClause())
