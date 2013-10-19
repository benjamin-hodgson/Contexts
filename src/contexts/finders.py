import glob
import importlib
import inspect
import os
import re
import types
from . import errors
from . import util


establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Gg]iven)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)[Cc]leanup")
spec_re = re.compile(r"([Ss]pec|[Ww]hen)")
module_re = re.compile(r"([Ss]pec|[Tt]est)")


def get_specs_from_modules(modules):
    for module in modules:
        for context in get_specs_from_module(module):
            yield context


def get_specs_from_module(module):
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if re.search(spec_re, name):
            yield cls()


def find_modules_in_directory(dir_path):
    if os.path.join(dir_path, "__init__.py") in glob.glob(os.path.join(dir_path, '*.py')):
        return import_modules_in_package(dir_path)
    return import_modules_in_directory(dir_path)

def import_modules_in_package(dir_path):
    imported_modules = []
    imported_modules.append(util.import_module_from_file(dir_path))
    for file_path in glob.iglob(os.path.join(dir_path, '*.py')):
        if "__init__.py" in file_path:
            continue
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        package_name = os.path.basename(dir_path)
        with util.prepend_folder_to_sys_dot_path(os.path.dirname(dir_path)):
            imported_modules.append(importlib.import_module(package_name + '.' + module_name))
    return imported_modules

def import_modules_in_directory(dir_path):
    imported_modules = []
    for file_path in glob.iglob(os.path.join(dir_path, '*.py')):
        if re.search(module_re, os.path.basename(file_path)):
            imported_modules.append(util.import_module_from_file(file_path))
    return imported_modules


# Refactoring hint: below this comment are functions that find special methods on an instance.
# Above it are functions that find modules from a directory. Perhaps the top half is
# an 'importer' object (which would incorporate at least some of the contents of 'util.py')
# and the bottom is something like a 'special method finder'.

def find_setups(spec):
    return find_methods_matching(spec, establish_re, top_down=True, one_per_class=True)


def find_actions(spec):
    return find_methods_matching(spec, because_re, one_only=True, one_per_class=True)


def find_assertions(spec):
    return find_methods_matching(spec, should_re)


def find_teardowns(spec):
    return find_methods_matching(spec, cleanup_re, one_per_class=True)


def find_methods_matching(spec, regex, *, top_down=False, one_only=False, one_per_class=False):
    found = []
    mro = spec.__class__.__mro__
    classes = reversed(mro) if top_down else mro
    for cls in classes:
        found.extend(find_methods_on_class_matching(cls, spec, regex, one_only or one_per_class))
        if one_only and found:
            break
    return found


def find_methods_on_class_matching(cls, instance, regex, one_per_class):
    found = []
    for name, func in cls.__dict__.items():
        if re.search(regex, name) and callable(func):
            method = types.MethodType(func, instance)
            found.append(method)

    if one_per_class:
        assert_single_method_of_given_type(cls, found)

    return found


def assert_single_method_of_given_type(cls, found):
    if len(found) > 1:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += ", ".join([meth.__func__.__name__ for meth in found])
        raise errors.TooManySpecialMethodsError(msg)
