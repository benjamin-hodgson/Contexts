import collections
import os
import types
from .core import Suite
from . import finders
from . import discovery


def build_suite(spec):
    """
    Polymorphic suite-building function.

    build_suite(class) - return a suite containing the test class
    build_suite(module) - return a suite containing all the test classes in the module
    build_suite(file_path:string) - return a suite containing all the test classes found in the file
    build_suite(folder_path:string) - return a suite composed of all the test files in the folder
    build_suite(package_path:string) - return a suite composed of all the test files in the package
    """
    if isinstance(spec, types.ModuleType):
        return build_suite_from_module(spec)
    elif isinstance(spec, str) and os.path.isfile(spec):
        return build_suite_from_file_path(spec)
    elif isinstance(spec, str) and os.path.isdir(spec):
        return build_suite_from_directory_path(spec)
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
