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


class WhenUserExpicitlyAssertsFalse(AssertionRewritingSharedContext):
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


class WhenUserAssertsOnAnArbitraryObject(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_object"
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        self.code = """
class Thing(object):
    def __bool__(self):
        return False

a_thing = Thing()

class TestSpec:
    def it(self):
        assert a_thing
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self):
        a_thing = sys.modules[self.module_name].a_thing
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {} but found it not to be truthy".format(repr(a_thing)))


class WhenUserAssertsOnAFunctionCall(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_function_call"
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        self.code = """
from unittest import mock

m = mock.Mock(return_value=False)

class TestSpec:
    def it(self):
        assert m()
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {} but found it not to be truthy".format(False))


class WhenUserAssertsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_equal.py")
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


class WhenUserAssertsEqualOnAFunctionCallOnTheLeft(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.module_name = "assert_equal_func_left"
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

class TestSpec:
    def it(self):
        assert m() == {1}
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y)))


class WhenUserAssertsEqualOnAFunctionCallOnTheRight(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.module_name = "assert_equal_func_right"
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

class TestSpec:
    def it(self):
        assert {1} == m()
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} == {1} but found them not to be equal".format(repr(y), repr(x)))


class WhenUserAssertsNotEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 1
        yield 12.3
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

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


class WhenUserAssertsLessThanButItIsGreater(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_less_than_is_greater.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a < b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} < {1} but found it to be greater".format(repr(x), repr(y)))


class WhenUserAssertsLessThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_less_than_is_equal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {0}
        assert a < b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        print(self.reporter.calls[1])
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} < {0} but found them to be equal".format(repr(x)))


class WhenUserAssertsLessThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_less_than_or_equal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a <= b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} <= {1} but found it to be greater".format(repr(x), repr(y)))


class WhenUserAssertsGreaterThanButItIsLess(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_greater_than_is_less.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a > b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} > {1} but found it to be less".format(repr(x), repr(y)))


class WhenUserAssertsGreaterThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_greater_than_is_equal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {0}
        assert a > b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        print(self.reporter.calls[1])
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} > {0} but found them to be equal".format(repr(x)))


class WhenUserAssertsGreaterThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples(self):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.filename = os.path.join(TEST_DATA_DIR, "assert_greater_than_or_equal.py")
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a >= b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_assertion_failed(self):
        [call[0] for call in self.reporter.calls].should.contain('assertion_failed')

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        str(the_call[2]).should.equal("Asserted {0} >= {1} but found it to be less".format(repr(x), repr(y)))
