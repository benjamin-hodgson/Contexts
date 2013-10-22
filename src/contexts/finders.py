import inspect
import os
import re
import types
from collections import namedtuple
from . import errors


# This class needs a tidy up
class ModuleFinder(object):
    ModuleSpecification = namedtuple('ModuleSpecification', ['parent_folder', 'module_name'])

    file_re = re.compile(r"([Ss]pec|[Tt]est).*?\.py$")
    folder_re = re.compile(r"([Ss]pec|[Tt]est)")

    def __init__(self, directory):
        self.directory = directory

    def find_modules(self):
        module_specs = []

        for dirpath, dirnames, filenames in os.walk(self.directory):
            self.remove_non_test_folders(dirnames)
            if ispackage(dirpath):
                package_spec = self.get_package_specification(dirpath)
                module_specs.append(package_spec)
                found_modules = self.get_modules(filenames, package_spec[0], package_spec[1] + '.')
            else:
                found_modules = self.get_modules(filenames, dirpath)
            
            module_specs.extend(found_modules)

        return module_specs

    @classmethod
    def remove_non_test_folders(cls, dirnames):
        dirnames[:] = [n for n in dirnames if cls.folder_re.search(n)]

    @classmethod
    def get_modules(cls, filenames, dirpath, package_prefix=''):
        module_names = (remove_extension(f) for f in filenames if cls.file_re.search(f))
        full_names = (package_prefix + m for m in module_names)
        return (cls.ModuleSpecification(dirpath, n) for n in full_names)

    @classmethod
    def get_package_specification(cls, dirpath):
        parent = os.path.dirname(dirpath)
        package_names = [os.path.basename(dirpath)]

        while ispackage(parent):
            dirpath, parent = parent, os.path.dirname(parent)
            package_names.append(os.path.basename(dirpath))
        
        full_package_name = '.'.join(reversed(package_names))
        return cls.ModuleSpecification(parent, full_package_name)


def ispackage(directory):
    return "__init__.py" in os.listdir(directory)


def remove_extension(filename):
    basename = os.path.basename(filename)
    name, extension = os.path.splitext(basename)
    return name


class ClassFinder(object):
    class_re = re.compile(r"([Ss]pec|[Ww]hen)")

    def find_specs_in_modules(self, modules):
        for module in modules:
            for context in self.find_specs_in_module(module):
                yield context


    def find_specs_in_module(self, module):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if self.class_re.search(name):
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
            if regex.search(name) and callable(func):
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
