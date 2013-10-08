import types
import collections
from .core import Suite, Context, Assertion
from . import finders


def build_suite(obj):
    if isinstance(obj, collections.Iterable):
        return Suite([build_context(x) for x in obj])
    if isinstance(obj, types.ModuleType):
        contexts = finders.get_contexts_from_module(obj)
        return Suite([build_context(ctx) for ctx in contexts])
    return Suite([build_context(obj)])

def build_context(spec):
    setups = finders.find_methods_matching(spec, finders.establish_re, top_down=True)
    actions = finders.find_methods_matching(spec, finders.because_re, one_only=True)
    assertions = assertions = [Assertion(f) for f in finders.find_methods_matching(spec, finders.should_re)]
    teardowns = finders.find_methods_matching(spec, finders.cleanup_re)
    return Context(setups, actions, assertions, teardowns)
