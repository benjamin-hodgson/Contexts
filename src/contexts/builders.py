import collections
import itertools
import os
import types
from .core import Suite, Context, Assertion
from . import errors
from . import finders
from . import importers


def build_suite(spec):
    if isinstance(spec, types.ModuleType):
        return build_suite_from_module(spec)
    elif isinstance(spec, str) and os.path.isfile(spec):
        return build_suite_from_file_path(spec)
    elif isinstance(spec, str) and os.path.isdir(spec):
        return build_suite_from_directory_path(spec)
    elif isinstance(spec, collections.Iterable):
        return build_suite_from_iterable(spec)
    elif isinstance(spec, type):
        return build_suite_from_class(spec)
    else:
        return build_suite_from_instance(spec)


def build_suite_from_directory_path(dir_path):
    modules = importers.import_from_directory(dir_path)

    finder = finders.ClassFinder()
    specs = finder.find_specs_in_modules(modules)
    return build_suite_from_iterable(specs)


def build_suite_from_file_path(filepath):
    folder = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    module_name = os.path.splitext(filename)[0]
    module = importers.load_module(folder, module_name)
    return build_suite_from_module(module)


def build_suite_from_module(module):
    finder = finders.ClassFinder()
    specs = finder.find_specs_in_module(module)
    return build_suite_from_iterable(specs)


def build_suite_from_iterable(specs):
    contexts = [build_context(x) for x in specs]
    return Suite(contexts)


def build_suite_from_class(cls):
    return build_suite_from_instance(cls())


def build_suite_from_instance(spec):
    contexts = [build_context(spec)]
    return Suite(contexts)


def build_context(spec):
    finder = finders.MethodFinder(spec)

    setups, actions, assertions, teardowns = finder.find_special_methods()
    assert_no_ambiguous_methods(setups, actions, assertions, teardowns)

    wrapped_assertions = [Assertion(f, build_assertion_name(f)) for f in assertions]

    return Context(setups, actions, wrapped_assertions, teardowns, spec.__class__.__name__)


def build_assertion_name(func):
    module_name = func.__module__
    method_name = func.__qualname__
    return '{}.{}'.format(module_name, method_name)


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
