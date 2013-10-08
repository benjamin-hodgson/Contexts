import types
import collections
from .core import Suite, Context
from .finder import get_contexts_from_module


def build_suite(obj):
    if isinstance(obj, collections.Iterable):
        return Suite([Context(x) for x in obj])
    if isinstance(obj, types.ModuleType):
        contexts = get_contexts_from_module(obj)
        return Suite([Context(ctx) for ctx in contexts])
    return Suite([Context(obj)])
