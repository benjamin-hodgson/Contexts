import os
import shutil
import sys
import sure
from .tools import SpyReporter
import contexts


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data", "assertion_rewriting_test_data")


class WhenUserSuppliesAnAssertionMessage:
    def establish_that_there_is_a_test_file(self):
        self.old_sys_dot_modules = sys.modules.copy()

        self.filename = os.path.join(TEST_DATA_DIR, "explicit_message_test.py")
        self.message = "i asserted false :("
        code = """
class TestSpec:
    def it(self):
        assert False, {}
""".format(repr(self.message))

        self.write_file(code)

        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_the_supplied_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal(self.message)

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        sys.modules = self.old_sys_dot_modules
        shutil.rmtree(TEST_DATA_DIR)

    def write_file(self, code):
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(code)


class WhenUserAssertsFalse:
    def context(self):
        self.old_sys_dot_modules = sys.modules.copy()

        self.filename = os.path.join(TEST_DATA_DIR, "assert_false.py")
        code = """
class TestSpec:
    def it(self):
        assert False
"""

        self.write_file(code)

        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Explicitly asserted False")

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        sys.modules = self.old_sys_dot_modules
        shutil.rmtree(TEST_DATA_DIR)

    def write_file(self, code):
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(code)


class WhenUserAssertsEqualWithLiterals:
    @classmethod
    def examples(cls):
        yield 1, 2
        yield 5, 12
        yield 'a', 'b'
        yield 12.3, 5.1
        yield 'x', 1

    def context(self, x, y):
        self.old_sys_dot_modules = sys.modules.copy()

        self.filename = os.path.join(TEST_DATA_DIR, "assert_false.py")
        code = """
class TestSpec:
    def it(self):
        assert {0} == {1}
""".format(repr(x), repr(y))
        self.write_file(code)

        self.reporter = SpyReporter()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} == {1} but found {0} != {1}.".format(repr(x), repr(y)))

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        sys.modules = self.old_sys_dot_modules
        shutil.rmtree(TEST_DATA_DIR)

    def write_file(self, code):
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(code)
