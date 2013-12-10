import os
import shutil
import sys
import sure
from .tools import SpyReporter
import contexts


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data", "assertion_rewriting_test_data")


class AssertionRewritingSharedContext:
    def establish(self):
        self.old_sys_dot_modules = sys.modules.copy()
        self.reporter = SpyReporter()

    def write_file(self):
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(self.code)

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        sys.modules = self.old_sys_dot_modules
        shutil.rmtree(TEST_DATA_DIR)


class WhenUserSuppliesAnAssertionMessage(AssertionRewritingSharedContext):
    def establish_that_there_is_a_test_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, "explicit_message_test.py")
        self.message = "i asserted false :("
        self.code = """
class TestSpec:
    def it(self):
        assert False, {}
""".format(repr(self.message))

        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_the_supplied_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal(self.message)


class WhenUserAssertsFalse(AssertionRewritingSharedContext):
    def context(self):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_false.py")
        self.code = """
class TestSpec:
    def it(self):
        assert False
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Explicitly asserted False")


class WhenUserAssertsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1, 2
        yield 5, 12
        yield 'a', 'b'
        yield 12.3, 5.1
        yield 'x', 1
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_equal_literal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a == b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y)))


class WhenUserAssertsNotEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 13
        yield 'x'
        yield {'abc':[123, None]}
    def context(self, x):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_not_equal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = b = {}
        assert a != b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} != {0} but found them to be equal".format(repr(x)))
