import types
import collections
import itertools
from .core import Suite, Context, Assertion
from . import finders
from . import errors


def build_suite(obj):
    if isinstance(obj, collections.Iterable):
        return build_suite_from_iterable(obj)
    if isinstance(obj, types.ModuleType):
        return build_suite_from_module(obj)
    return build_suite_from_single_class(obj)


def build_suite_from_iterable(iterable):
    contexts = [build_context(x) for x in iterable]
    return Suite(contexts)


def build_suite_from_module(module):
    classes = finders.get_contexts_from_module(module)
    contexts = [build_context(cls) for cls in classes]
    return Suite(contexts)


def build_suite_from_single_class(cls):
    contexts = [build_context(cls)]
    return Suite(contexts)


def build_context(cls):
    setups = finders.find_setups(cls)
    actions = finders.find_actions(cls)
    assertions = finders.find_assertions(cls)
    teardowns = finders.find_teardowns(cls)

    assert_no_ambiguous_methods(setups, actions, assertions, teardowns)

    wrapped_assertions = [Assertion(f, build_assertion_name(f)) for f in assertions]
    return Context(setups, actions, wrapped_assertions, teardowns)


def build_assertion_name(func):
    module_name = func.__self__.__class__.__module__
    method_name = func.__func__.__qualname__
    return '{}.{}\n'.format(module_name, method_name)


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
