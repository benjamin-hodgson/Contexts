import itertools
import os
import re
from collections import namedtuple


PackageSpecification = namedtuple('PackageSpecification', ['parent_folder', 'package_name'])
ModuleSpecification = namedtuple('ModuleSpecification', ['parent_folder', 'module_name'])

file_re = re.compile(r"([Ss]pec|[Tt]est).*?\.py$")
folder_re = re.compile(r"([Ss]pec|[Tt]est)")


def find_modules(directory):
    finders = FinderGenerator.walk_and_generate(directory)
    return itertools.chain.from_iterable(finder.find_modules() for finder in finders)


class FinderGenerator(object):
    """Like a finder factory, but generates a sequence of them"""
    @classmethod
    def walk_and_generate(cls, directory):
        gen = cls(directory)
        return gen.generate_finders()

    def __init__(self, starting_directory):
        self.walker = Walker(starting_directory)

    def generate_finders(self):
        while True:
            # let StopIteration bubble up from
            # self.walker to whoever's iterating
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
        for filename in matching_filenames(self.directory):
            yield remove_extension(filename)


class PackageModuleFinder(object):
    def __init__(self, directory):
        self.directory = directory
        self.package_spec = PackageSpecificationFactory(self.directory).create()

    def find_modules(self):
        found_modules = self.get_module_names()
        specs = (ModuleSpecification(self.package_spec[0], mod) for mod in found_modules)
        return itertools.chain([self.package_spec], specs)

    def get_module_names(self):
        for filename in matching_filenames(self.directory):
            module_name = remove_extension(filename)
            yield self.package_spec[1] + '.' + module_name


class PackageSpecificationFactory(object):
    def __init__(self, directory):
        self.directory = directory
        self.current_parent = os.path.dirname(directory)
        self.package_names = [os.path.basename(directory)]

    def create(self):
        self.traverse_filesystem()
        full_package_name = '.'.join(reversed(self.package_names))
        return PackageSpecification(self.current_parent, full_package_name)

    def traverse_filesystem(self):
        while ispackage(self.current_parent):
            dirpath, self.current_parent = self.current_parent, os.path.dirname(self.current_parent)
            self.package_names.append(os.path.basename(dirpath))


def ispackage(directory):
    return "__init__.py" in os.listdir(directory)


def matching_filenames(directory):
    for filename in os.listdir(directory):
        if file_re.search(filename):
            yield filename


def remove_non_test_folders(dirnames):
    dirnames[:] = [n for n in dirnames if folder_re.search(n)]


def remove_extension(filename):
    name, extension = os.path.splitext(filename)
    return name
