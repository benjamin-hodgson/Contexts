import os
import shutil
import sys
from .tools import SpyReporter
import contexts
from contexts.configuration import Configuration


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data", "assertion_rewriting_test_data")


class AssertionRewritingSharedContext:
    def establish(self):
        self.old_sys_dot_modules = sys.modules.copy()
        self.reporter = SpyReporter()

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(self.code)

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        del sys.modules[self.module_name]
        shutil.rmtree(TEST_DATA_DIR)


class WhenUserSuppliesAnAssertionMessage(AssertionRewritingSharedContext):
    def establish_that_there_is_a_test_file(self):
        self.module_name = "explicit_message_test"
        self.message = "i asserted false :("
        self.code = """
class TestSpec:
    def it(self):
        assert False, {}
""".format(repr(self.message))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_the_supplied_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == self.message


class WhenAssertionRewritingIsDisabled(AssertionRewritingSharedContext):
    def establish_that_there_is_a_test_file(self):
        self.module_name = "disabled"
        self.code = """
class TestSpec:
    def it(self):
        assert False
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=False))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_an_empty_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == ''


class WhenUserExpicitlyAssertsFalse(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_false"
        self.code = """
class TestSpec:
    def it(self):
        assert False
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Explicitly asserted False"


class WhenUserAssertsOnSomethingFalsy(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_falsy(cls):
        yield 0
        yield 0 + 0j
        yield ''
        yield {}
        yield []

    def context(self, x):
        self.module_name = "assert_not_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {}
        assert a
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {} but found it to be falsy".format(repr(x))



class WhenUserAssertsOnACustomObject(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_object"
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
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self):
        a_thing = sys.modules[self.module_name].a_thing
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {} but found it to be falsy".format(repr(a_thing))


class WhenUserAssertsNot(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_truthy(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield {'fantastic':'wonderful'}
        yield [{}]

    def context(self, x):
        self.module_name = "assert_not_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {}
        assert not a
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted not {} but found it to be truthy".format(repr(x))


class WhenUserAssertsOnAFunctionCall(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_function_call"
        self.code = """
from unittest import mock

m = mock.Mock(return_value=False)

class TestSpec:
    def it(self):
        assert m()
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {} but found it to be falsy".format(False)


class WhenUserAssertsOnAMethodCall(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_method_call"
        self.code = """
from unittest import mock

m = mock.Mock()
m.meth.return_value = False

class TestSpec:
    def it(self):
        assert m.meth()
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.meth.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {} but found it to be falsy".format(False)


class WhenUserAssertsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.module_name = "assert_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a == b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y))


class WhenUserAssertsEqualOnACustomObject(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.module_name = "assert_equal_custom_object"
        self.code = """
class NeverEqual(object):
    def __eq__(self, other):
        return False

never_equal = NeverEqual()

class TestSpec:
    def it(self):
        a = {0}
        assert a == never_equal
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        never_equal = sys.modules[self.module_name].never_equal
        assert str(the_call[2]) == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(never_equal))


class WhenUserAssertsEqualOnAFunctionCallOnTheLeft(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.module_name = "assert_equal_func_left"
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

class TestSpec:
    def it(self):
        assert m() == {1}
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y))


class WhenUserAssertsEqualOnAFunctionCallOnTheRight(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.module_name = "assert_equal_func_right"
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

class TestSpec:
    def it(self):
        assert {1} == m()
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_only_call_the_function_once(self):
        mock = sys.modules[self.module_name].m
        mock.assert_called_once_with()

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} == {1} but found them not to be equal".format(repr(y), repr(x))


class WhenUserAssertsNotEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.module_name = "assert_not_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = b = {}
        assert a != b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} != {0} but found them to be equal".format(repr(x))


class WhenUserAssertsLessThanButItIsGreater(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_greater_than_their_partners(cls):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.module_name = "assert_less_than_is_greater"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a < b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} < {1} but found it to be greater".format(repr(x), repr(y))


class WhenUserAssertsLessThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.module_name = "assert_less_than_is_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {0}
        assert a < b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} < {0} but found them to be equal".format(repr(x))


class WhenUserAssertsLessThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_greater_than_their_partners(cls):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.module_name = "assert_less_than_or_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a <= b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} <= {1} but found it to be greater".format(repr(x), repr(y))


class WhenUserAssertsGreaterThanButItIsLess(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_less_than_their_partners(cls):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.module_name = "assert_greater_than_is_less"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a > b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} > {1} but found it to be less".format(repr(x), repr(y))


class WhenUserAssertsGreaterThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.module_name = "assert_greater_than_is_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {0}
        assert a > b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} > {0} but found them to be equal".format(repr(x))


class WhenUserAssertsGreaterThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_less_than_their_partners(self):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.module_name = "assert_greater_than_or_equal"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a >= b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} >= {1} but found it to be less".format(repr(x), repr(y))


class WhenUserAssertsIn(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_contained_by_their_partners(cls):
        yield 1, [2]
        yield 12.3, {18.4: 'hello'}
        yield 'a', 'zbc'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.module_name = "assert_in"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a in b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} in {1} but found it not to be present".format(repr(x), repr(y))


class WhenUserAssertsNotIn(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_contained_by_their_partners(cls):
        yield 1, [1,2,'z']
        yield 12.3, {18.4: 'hello', 12.3: 'there'}
        yield 'a', 'zabc'
        yield (1, 3), (2, 1, (1, 3))

    def context(self, x, y):
        self.module_name = "assert_not_in"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a not in b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} not in {1} but found it to be present".format(repr(x), repr(y))


class WhenUserAssertsIs(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_their_partners(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        # objects that compare equal but are not the same object
        yield {'fantastic':'wonderful'}, {'fantastic':'wonderful'}

    def context(self, x, y):
        self.module_name = "assert_is"
        self.code = """
class TestSpec:
    def it(self):
        a = {0}
        b = {1}
        assert a is b
""".format(repr(x), repr(y))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, y):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} is {1} but found them not to be the same".format(repr(x), repr(y))


class WhenUserAssertsIsNot(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_themselves(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.module_name = "assert_is_not"
        self.code = """
class TestSpec:
    def it(self):
        a = b = {}
        assert a is not b
""".format(repr(x))
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted {0} is not {0} but found them to be the same".format(repr(x))


class WhenUserAssertsIsinstance(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_instances_of_their_partners(cls):
        yield 12.3, int
        yield {'abc'}, list
        yield "hello", set

    def context(self, x, cls):
        self.module_name = "assert_isinstance"
        self.code = """
class TestSpec:
    def it(self):
        a = {}
        b = {}
        assert isinstance(a, b)
""".format(repr(x), cls.__name__)
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, cls):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted isinstance({0}, {1}) but found it to be a {2}".format(repr(x), cls.__name__, type(x).__name__)


class WhenUserAssertsIsinstanceWithATuple(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_instances_of_their_partners(cls):
        yield 12.3, "(int, complex)"
        yield {'abc'}, "(list, dict)"
        yield "hello", "(set, bytes, float)"

    def context(self, x, tup):
        self.module_name = "assert_isinstance_tuple"
        self.code = """
class TestSpec:
    def it(self):
        a = {}
        b = {}
        assert isinstance(a, b)
""".format(repr(x), tup)
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self, x, tup):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        assert str(the_call[2]) == "Asserted isinstance({0}, {1}) but found it to be a {2}".format(repr(x), tup, type(x).__name__)


class WhenUserAssertsOnAChainedComparison(AssertionRewritingSharedContext):
    def context(self):
        self.module_name = "assert_chained_comparison"
        self.code = """
class TestSpec:
    def it(self):
        a = 3
        b = 1.1
        assert a < b < 12
"""
        self.write_file()

    def because_we_run_the_spec(self):
        contexts.run(self.filename, [self.reporter], config=Configuration(shuffle=False, rewriting=True))

    def it_should_call_assertion_failed(self):
        assert 'assertion_failed' in [call[0] for call in self.reporter.calls]

    def the_exception_should_contain_a_generated_message(self):
        the_call, = [call for call in self.reporter.calls if call[0] == 'assertion_failed']
        # FIXME: this should have a more useful message.
        # At the moment, the test is just making sure that the message doesn't lie outright.
        assert str(the_call[2]) == "Asserted False but found it to be falsy"
