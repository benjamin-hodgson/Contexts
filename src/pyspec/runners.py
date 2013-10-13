import types
import collections
from . import builders


def run(spec=None, result=None):
    if spec is None:
        suite = builders.build_suite_from_module(spec)
    elif isinstance(spec, types.ModuleType):
        suite = builders.build_suite_from_module(spec)
    elif isinstance(spec, collections.Iterable):
        suite = builders.build_suite_from_iterable(spec)
    elif isinstance(spec, type):
        suite = builders.build_suite_from_class(spec)
    else:
        suite = builders.build_suite_from_instance(spec)
    suite.run(result)
