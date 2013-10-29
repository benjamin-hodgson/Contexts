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
    """Like a factory class, but generates a sequence of them"""
    def __init__(self, directory):
        self.directory = directory

    def generate_finders(self):
        return (self.create_module_finder(dirpath) for dirpath in self.walk_folders())

    def walk_folders(self):
        for dirpath, dirnames, _ in os.walk(self.directory):
            self.remove_non_test_folders(dirnames)
            yield dirpath

    @classmethod
    def remove_non_test_folders(cls, dirnames):
        dirnames[:] = [n for n in dirnames if folder_re.search(n)]


    def create_module_finder(self, dirpath):
        if ispackage(dirpath):
            return PackageModuleFinder(dirpath)
        return FolderModuleFinder(dirpath)


class ModuleFinderBase(object):
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_module_names(self, filenames, directory, package_prefix=''):
        module_names = (remove_extension(f) for f in filenames if file_re.search(f))
        full_names = (package_prefix + m for m in module_names)
        return (ModuleSpecification(directory, n) for n in full_names)


class FolderModuleFinder(ModuleFinderBase):
    def find_modules(self):
        names = os.listdir(self.folder_path)
        return self.get_module_names(names, self.folder_path)


class PackageModuleFinder(ModuleFinderBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.package_spec = self.get_package_specification()
        self.specs = [self.package_spec]

    def find_modules(self):
        names = os.listdir(self.folder_path)
        found_modules = self.get_module_names(names, self.package_spec[0], self.package_spec[1] + '.')
        self.specs.extend(found_modules)
        return self.specs

    def get_package_specification(self):
        parent = os.path.dirname(self.folder_path)
        package_names = [os.path.basename(self.folder_path)]

        while ispackage(parent):
            dirpath, parent = parent, os.path.dirname(parent)
            package_names.append(os.path.basename(dirpath))

        full_package_name = '.'.join(reversed(package_names))
        return PackageSpecification(parent, full_package_name)


def ispackage(directory):
    return "__init__.py" in os.listdir(directory)


def remove_extension(filename):
    basename = os.path.basename(filename)
    name, extension = os.path.splitext(basename)
    return name
