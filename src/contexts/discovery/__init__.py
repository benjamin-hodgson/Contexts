import contextlib
import importlib
import itertools
import os
import re
import sys
from collections import namedtuple


PackageSpecification = namedtuple('PackageSpecification', ['parent_folder', 'package_name'])
ModuleSpecification = namedtuple('ModuleSpecification', ['parent_folder', 'module_name'])

file_re = re.compile(r"([Ss]pec|[Tt]est).*?\.py$")
folder_re = re.compile(r"([Ss]pec|[Tt]est)")


def import_from_file(file_path):
    """
    Import the specified file, with an unqualified module name.
    """
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return load_module(folder, module_name)


def load_module(dir_path, module_name):
    """
    Load specified module from the specified directory
    """
    prune_sys_dot_modules(dir_path, module_name)
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


def find_modules(directory):
    """
    Return an iterable of ModuleSpecifications found in the folder
    """
    finders = FinderGenerator(directory).generate_finders()
    return itertools.chain.from_iterable(finder.find_modules() for finder in finders)


def prune_sys_dot_modules(dir_path, module_name):
    requested_file = os.path.join(dir_path, module_name + '.py')
    if module_name in sys.modules:
        existing_module = sys.modules[module_name]
        if not same_file(existing_module.__file__, requested_file):
            del sys.modules[module_name]
            importlib.invalidate_caches()


@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)


def same_file(path1, path2):
    return os.path.realpath(path1) == os.path.realpath(path2)


class FinderGenerator(object):
    """Like a finder factory, but generates a sequence of them"""
    def __init__(self, starting_directory):
        self.walker = Walker(starting_directory)

    def generate_finders(self):
        for directory in self.walker:
            self.current_directory = directory
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
        return (ModuleSpecification(self.directory, mod) for mod in self.get_module_names())

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
