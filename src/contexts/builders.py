import collections
import os
import types
from .core import Suite
from . import finders
from . import discovery


def build_suite(spec):
    if isinstance(spec, types.ModuleType):
        return build_suite_from_module(spec)
    elif isinstance(spec, str) and os.path.isfile(spec):
        return build_suite_from_file_path(spec)
    elif isinstance(spec, str) and os.path.isdir(spec):
        return build_suite_from_directory_path(spec)
    elif isinstance(spec, collections.Iterable):
        return Suite(spec)
    elif isinstance(spec, type):
        return Suite([spec])


def build_suite_from_directory_path(dir_path):
    modules = discovery.import_from_directory(dir_path)
    finder = finders.ClassFinder()
    classes = finder.find_specs_in_modules(modules)
    return Suite(classes)


def build_suite_from_file_path(filepath):
    module = discovery.import_from_file(filepath)
    return build_suite_from_module(module)


def build_suite_from_module(module):
    finder = finders.ClassFinder()
    classes = finder.find_specs_in_module(module)
    return Suite(classes)
