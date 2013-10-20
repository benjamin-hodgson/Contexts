import glob
import inspect
import os
import re
import types
from collections import namedtuple
from . import errors


spec_re = re.compile(r"([Ss]pec|[Ww]hen)")
module_re = re.compile(r"([Ss]pec|[Tt]est)")


###########################################################
# Finding modules
###########################################################

def find_modules_in_directory(dir_path):
    found_modules = []
    for file_path in glob.iglob(os.path.join(dir_path, '*.py')):
        if re.search(module_re, os.path.basename(file_path)):
            found_modules.append(file_path)
    return found_modules


def find_modules_in_package(package_path):
    found_module_names = []

    package_name = os.path.basename(package_path)
    for file_path in glob.iglob(os.path.join(package_path, '*.py')):
        if "__init__.py" in file_path:
            continue
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        found_module_names.append(package_name + '.' + module_name)

    return found_module_names


###########################################################
# Finding classes
###########################################################

def find_specs_in_modules(modules):
    for module in modules:
        for context in find_specs_in_module(module):
            yield context


def find_specs_in_module(module):
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if re.search(spec_re, name):
            yield cls()


class MethodFinder(object):
    SpecialMethods = namedtuple("SpecialMethods", ['setups', 'actions', 'assertions', 'teardowns'])

    establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Gg]iven)")
    because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
    should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
    cleanup_re = re.compile(r"(^|_)[Cc]leanup")

    def __init__(self, spec):
        self.spec = spec

    def find_special_methods(self):
        return self.SpecialMethods(
            self.find_setups(),
            self.find_actions(),
            self.find_assertions(),
            self.find_teardowns())

    def find_setups(self):
        return self.find_methods_matching(self.establish_re, top_down=True, one_per_class=True)

    def find_actions(self):
        return self.find_methods_matching(self.because_re, one_only=True, one_per_class=True)

    def find_assertions(self):
        return self.find_methods_matching(self.should_re)

    def find_teardowns(self):
        return self.find_methods_matching(self.cleanup_re, one_per_class=True)

    def find_methods_matching(self, regex, *, top_down=False, one_only=False, one_per_class=False):
        found = []
        mro = self.spec.__class__.__mro__
        classes = reversed(mro) if top_down else mro
        for cls in classes:
            found.extend(self.find_methods_on_class_matching(cls, regex, one_only or one_per_class))
            if one_only and found:
                break
        return found

    def find_methods_on_class_matching(self, cls, regex, one_per_class):
        found = []
        for name, func in cls.__dict__.items():
            if re.search(regex, name) and callable(func):
                method = types.MethodType(func, self.spec)
                found.append(method)

        if one_per_class:
            assert_single_method_of_given_type(cls, found)

        return found


def assert_single_method_of_given_type(cls, found):
    if len(found) > 1:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += ", ".join([meth.__func__.__name__ for meth in found])
        raise errors.TooManySpecialMethodsError(msg)
