import types
import collections
import itertools
from .core import Suite, Context, Assertion
from . import finders
from . import errors


def build_suite(obj):
    if isinstance(obj, collections.Iterable):
        return Suite([build_context(x) for x in obj])
    if isinstance(obj, types.ModuleType):
        contexts = finders.get_contexts_from_module(obj)
        return Suite([build_context(ctx) for ctx in contexts])
    return Suite([build_context(obj)])


def build_context(spec):
    setups = finders.find_setups(spec)
    actions = finders.find_actions(spec)
    assertions = finders.find_assertions(spec)
    teardowns = finders.find_teardowns(spec)

    assert_no_duplicate_entries(setups, actions, assertions, teardowns)

    return Context(setups, actions, [Assertion(f) for f in assertions], teardowns)


def assert_no_duplicate_entries(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
