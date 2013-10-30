import itertools
import os
import re
from collections import namedtuple


PackageSpecification = namedtuple('PackageSpecification', ['parent_folder', 'package_name'])
ModuleSpecification = namedtuple('ModuleSpecification', ['parent_folder', 'module_name'])

file_re = re.compile(r"([Ss]pec|[Tt]est).*?\.py$")
folder_re = re.compile(r"([Ss]pec|[Tt]est)")


def find_modules(directory):
    finders = generate_finders(directory)
    return itertools.chain.from_iterable(finder.find_modules() for finder in finders)


def generate_finders(directory):
    gen = FinderGenerator(directory)
    return gen.generate_finders()


class FinderGenerator(object):
    """Like a finder factory, but generates a sequence of them"""
    def __init__(self, starting_directory):
        self.walker = Walker(starting_directory)

    def generate_finders(self):
        while True:
            self.current_directory = next(self.walker)
            yield self.create_finder()

    def create_finder(self):
        if ispackage(self.current_directory):
            return PackageModuleFinder(self.current_directory)
        return FolderModuleFinder(self.current_directory)


def Walker(starting_directory):
    for dirpath, dirnames, _ in os.walk(starting_directory):
        remove_non_test_folders(dirnames)
        yield dirpath


class FolderModuleFinder(object):
    def __init__(self, directory):
        self.directory = directory

    def find_modules(self):
        found_modules = self.get_module_names()
        return (ModuleSpecification(self.directory, mod) for mod in found_modules)

    def get_module_names(self):
        for name in os.listdir(self.directory):
            if file_re.search(name):
                yield remove_extension(name)


class PackageModuleFinder(object):
    def __init__(self, directory):
        self.directory = directory
        self.package_spec = self.get_package_specification()

    def find_modules(self):
        found_modules = self.get_module_names()
        specs = (ModuleSpecification(self.package_spec[0], mod) for mod in found_modules)
        return itertools.chain([self.package_spec], specs)

    def get_module_names(self):
        for filename in os.listdir(self.directory):
            if file_re.search(filename):
                module_name = remove_extension(filename)
                yield self.package_spec[1] + '.' + module_name

    def get_package_specification(self):
        parent = os.path.dirname(self.directory)
        package_names = [os.path.basename(self.directory)]

        while ispackage(parent):
            dirpath, parent = parent, os.path.dirname(parent)
            package_names.append(os.path.basename(dirpath))

        full_package_name = '.'.join(reversed(package_names))
        return PackageSpecification(parent, full_package_name)


def ispackage(directory):
    return "__init__.py" in os.listdir(directory)


def remove_non_test_folders(dirnames):
    dirnames[:] = [n for n in dirnames if folder_re.search(n)]


def remove_extension(filename):
    name, extension = os.path.splitext(filename)
    return name
