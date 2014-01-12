import importlib.machinery
import os
import sys
from .assertion_rewriting import AssertionRewritingLoader


class Importer:
    def __init__(self, rewriting):
        self.rewriting = rewriting

    def import_from_file(self, file_path):
        """
        Import the specified file, with an unqualified module name.
        """
        folder = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        module_name = os.path.splitext(filename)[0]
        return self.import_module(folder, module_name)

    def import_module(self, dir_path, module_name):
        """
        Import the specified module from the specified directory, rewriting
        assert statements where necessary.
        """
        filename = resolve_filename(dir_path, module_name)
        prune_sys_dot_modules(module_name, filename)
        if module_name in sys.modules:
            return sys.modules[module_name]

        loader = self.create_loader(module_name, filename)
        return loader.load_module(module_name)

    def create_loader(self, module_name, filename):
        if self.rewriting:
            return AssertionRewritingLoader(module_name, filename)
        return importlib.machinery.SourceFileLoader(module_name, filename)


def resolve_filename(dir_path, module_name):
    filename = os.path.join(dir_path, *module_name.split('.'))
    if os.path.isdir(filename):  # it's a package
        filename = os.path.join(filename, '__init__.py')
    else:
        filename += '.py'
    return filename


def prune_sys_dot_modules(module_name, module_location):
    if module_name in sys.modules:
        existing_module = sys.modules[module_name]
        if not same_file(existing_module.__file__, module_location):
            del sys.modules[module_name]


def same_file(path1, path2):
    return os.path.realpath(path1) == os.path.realpath(path2)
