import importlib
import os
import shutil
import sys
import contexts
from contexts import action, assertion
from contexts.plugins.importing.assertion_rewriting import AssertionRewritingImporter


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data", "assertion_rewriting_test_data")


class AssertionRewritingSharedContext:
    def establish(self):
        self.module_name = "assertion_rewriting_test_data"
        self.old_sys_dot_modules = sys.modules.copy()
        self.importer = AssertionRewritingImporter()

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        os.mkdir(TEST_DATA_DIR)
        with open(self.filename, 'w') as f:
            f.write(self.code)

    def cleanup_the_filesystem_and_sys_dot_modules(self):
        shutil.rmtree(TEST_DATA_DIR)
        del sys.modules[self.module_name]
        importlib.invalidate_caches()


class WhenUserSuppliesAnAssertionMessage(AssertionRewritingSharedContext):
    def establish_that_there_is_a_test_file(self):
        self.message = "i asserted false :("
        self.code = """
def assertion_func():
    assert False, {}
""".format(repr(self.message))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    def it_should_not_change_the_message(self):
        assert self.exc.args[0] == self.message


class WhenUserExpicitlyAssertsFalse(AssertionRewritingSharedContext):
    def context(self):
        self.code = """
def assertion_func():
    assert False
"""
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self):
        assert self.exc.args[0] == "Explicitly asserted False"


class WhenUserAssertsOnSomethingFalsy(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_falsy(cls):
        yield 0
        yield 0 + 0j
        yield ''
        yield {}
        yield []

    def context(self, x):
        self.code = """
def assertion_func():
    a = {}
    assert a
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted {} but found it to be falsy".format(repr(x))


class WhenUserAssertsOnACustomObject(AssertionRewritingSharedContext):
    def context(self):
        self.code = """
class Thing(object):
    def __bool__(self):
        return False

a_thing = Thing()

def assertion_func():
    assert a_thing
"""
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self):
        a_thing = self.module.a_thing
        assert self.exc.args[0] == "Asserted {} but found it to be falsy".format(repr(a_thing))


class WhenUserAssertsNot(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_truthy(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield {'fantastic':'wonderful'}
        yield [{}]

    def context(self, x):
        self.code = """
def assertion_func():
    a = {}
    assert not a
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted not {} but found it to be truthy".format(repr(x))


class WhenUserAssertsOnAFunctionCall(AssertionRewritingSharedContext):
    def context(self):
        self.code = """
from unittest import mock

m = mock.Mock(return_value=False)

def assertion_func():
    assert m()
"""
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    def it_should_only_call_the_function_once(self):
        self.module.m.assert_called_once_with()

    @assertion
    def the_exception_should_be_given_a_generated_message(self):
        assert self.exc.args[0] == "Asserted {} but found it to be falsy".format(False)


class WhenUserAssertsOnAMethodCall(AssertionRewritingSharedContext):
    def context(self):
        self.code = """
from unittest import mock

m = mock.Mock()
m.meth.return_value = False

def assertion_func():
    assert m.meth()
"""
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    def it_should_only_call_the_function_once(self):
        self.module.m.meth.assert_called_once_with()

    @assertion
    def the_exception_should_be_given_a_generated_message(self):
        assert self.exc.args[0] == "Asserted {} but found it to be falsy".format(False)


class WhenUserAssertsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a == b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y))


# this is a test for one of the weirdest bugs i've ever seen.
# Commented for now because i don't know how to fix it
# class WhenAnAssertionTakesUpMultipleLines(AssertionRewritingSharedContext):
#     def context(self):
#         self.code = """
# def assertion_func():
#     assert [123] == [
#         456
#     ]
# """
#         self.write_file()

#     @action
#     def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
#         self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
#         self.exc = contexts.catch(self.module.assertion_func)

#     def the_exception_should_have_the_correct_line_number(self):
#         tb = self.exc.__traceback__
#         bottom_frame = traceback.extract_tb(tb)[-1]
#         assert bottom_frame[1] == 3


class WhenUserAssertsEqualOnACustomObject(AssertionRewritingSharedContext):
    @classmethod
    def examples(cls):
        yield 1
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.code = """
class NeverEqual(object):
    def __eq__(self, other):
        return False

never_equal = NeverEqual()

def assertion_func():
    a = {0}
    assert a == never_equal
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        never_equal = self.module.never_equal
        assert self.exc.args[0] == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(never_equal))


class WhenUserAssertsEqualOnAFunctionCallOnTheLeft(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

def assertion_func():
    assert m() == {1}
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    def it_should_only_call_the_function_once(self):
        self.module.m.assert_called_once_with()

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} == {1} but found them not to be equal".format(repr(x), repr(y))


class WhenUserAssertsEqualOnAFunctionCallOnTheRight(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_equal(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        yield {'fantastic':'wonderful'}, {'fantastic':['not equal']}

    def context(self, x, y):
        self.code = """
from unittest import mock

m = mock.Mock(return_value = {0})

def assertion_func():
    assert {1} == m()
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    def it_should_only_call_the_function_once(self):
        self.module.m.assert_called_once_with()

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} == {1} but found them not to be equal".format(repr(y), repr(x))


class WhenUserAssertsNotEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.code = """
def assertion_func():
    a = b = {}
    assert a != b
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted {0} != {0} but found them to be equal".format(repr(x))


class WhenUserAssertsLessThanButItIsGreater(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_greater_than_their_partners(cls):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a < b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} < {1} but found it to be greater".format(repr(x), repr(y))


class WhenUserAssertsLessThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.code = """
def assertion_func():
    a = {0}
    b = {0}
    assert a < b
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted {0} < {0} but found them to be equal".format(repr(x))


class WhenUserAssertsLessThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_greater_than_their_partners(cls):
        yield 3, 1
        yield 52.9, 12.3
        yield 'z', 'a'
        yield (2, 1), (1, 3)

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a <= b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} <= {1} but found it to be greater".format(repr(x), repr(y))


class WhenUserAssertsGreaterThanButItIsLess(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_less_than_their_partners(cls):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a > b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} > {1} but found it to be less".format(repr(x), repr(y))


class WhenUserAssertsGreaterThanButItIsEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_equal_themselves(cls):
        yield 3
        yield 52.9
        yield 'z'
        yield (2, 1)

    def context(self, x):
        self.code = """
def assertion_func():
    a = {0}
    b = {0}
    assert a > b
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted {0} > {0} but found them to be equal".format(repr(x))


class WhenUserAssertsGreaterThanOrEqual(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_less_than_their_partners(self):
        yield 1, 2
        yield 12.3, 18.4
        yield 'a', 'z'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a >= b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} >= {1} but found it to be less".format(repr(x), repr(y))


class WhenUserAssertsIn(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_contained_by_their_partners(cls):
        yield 1, [2]
        yield 12.3, {18.4: 'hello'}
        yield 'a', 'zbc'
        yield (1, 3), (2, 1)

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a in b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} in {1} but found it not to be present".format(repr(x), repr(y))


class WhenUserAssertsNotIn(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_contained_by_their_partners(cls):
        yield 1, [1,2,'z']
        yield 12.3, {18.4: 'hello', 12.3: 'there'}
        yield 'a', 'zabc'
        yield (1, 3), (2, 1, (1, 3))

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a not in b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} not in {1} but found it to be present".format(repr(x), repr(y))


class WhenUserAssertsIs(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_their_partners(cls):
        yield 1, 2
        yield 'a', 'b'
        yield (), 3.2
        # objects that compare equal but are not the same object
        yield {'fantastic':'wonderful'}, {'fantastic':'wonderful'}

    def context(self, x, y):
        self.code = """
def assertion_func():
    a = {0}
    b = {1}
    assert a is b
""".format(repr(x), repr(y))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, y):
        assert self.exc.args[0] == "Asserted {0} is {1} but found them not to be the same".format(repr(x), repr(y))


class WhenUserAssertsIsNot(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_themselves(cls):
        yield 1
        yield 12.3
        yield 'a'
        yield ()
        yield {'fantastic':'wonderful'}

    def context(self, x):
        self.code = """
def assertion_func():
    a = b = {}
    assert a is not b
""".format(repr(x))
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x):
        assert self.exc.args[0] == "Asserted {0} is not {0} but found them to be the same".format(repr(x))


class WhenUserAssertsIsinstance(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_instances_of_their_partners(cls):
        yield 12.3, int
        yield {'abc'}, list
        yield "hello", set

    def context(self, x, cls):
        self.code = """
def assertion_func():
    a = {}
    b = {}
    assert isinstance(a, b)
""".format(repr(x), cls.__name__)
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, cls):
        assert self.exc.args[0] == "Asserted isinstance({0}, {1}) but found it to be a {2}".format(repr(x), cls.__name__, type(x).__name__)


class WhenUserAssertsIsinstanceWithATuple(AssertionRewritingSharedContext):
    @classmethod
    def examples_of_things_that_are_not_instances_of_their_partners(cls):
        yield 12.3, "(int, complex)"
        yield {'abc'}, "(list, dict)"
        yield "hello", "(set, bytes, float)"

    def context(self, x, tup):
        self.code = """
def assertion_func():
    a = {}
    b = {}
    assert isinstance(a, b)
""".format(repr(x), tup)
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self, x, tup):
        assert self.exc.args[0] == "Asserted isinstance({0}, {1}) but found it to be a {2}".format(repr(x), tup, type(x).__name__)


class WhenUserAssertsOnAChainedComparison(AssertionRewritingSharedContext):
    def context(self):
        self.code = """
def assertion_func():
    a = 3
    b = 1.1
    assert a < b < 12
"""
        self.write_file()

    @action
    def when_we_import_the_module_and_prompt_it_to_raise_the_exception(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)
        self.exc = contexts.catch(self.module.assertion_func)

    @assertion
    def the_exception_should_be_given_a_generated_message(self):
        # FIXME: this should have a more useful message.
        # At the moment, the test is just making sure that the message doesn't lie outright.
        assert self.exc.args[0] == "Asserted False but found it to be falsy"
