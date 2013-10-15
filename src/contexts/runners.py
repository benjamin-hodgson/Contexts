import collections
import types
from . import builders


def run(spec, result):
    if isinstance(spec, types.ModuleType):
        suite = builders.build_suite_from_module(spec)
    elif isinstance(spec, str):
        suite = builders.build_suite_from_file_path(spec)
    elif isinstance(spec, collections.Iterable):
        suite = builders.build_suite_from_iterable(spec)
    elif isinstance(spec, type):
        suite = builders.build_suite_from_class(spec)
    else:
        suite = builders.build_suite_from_instance(spec)
    suite.run(result)
