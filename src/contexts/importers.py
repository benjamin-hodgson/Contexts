import contextlib
import importlib
import os
import sys
from . import finders


def import_from_directory(dir_path):
    finder = finders.ModuleFinder(dir_path)
    module_specs = finder.find_modules()
    return (load_module(*spec) for spec in module_specs)


def load_module(dir_path, module_name):
    prune_sys_dot_modules(dir_path, module_name)
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


def prune_sys_dot_modules(dir_path, module_name):
    requested_file = os.path.join(dir_path, module_name + '.py')
    if module_name in sys.modules:
        same_file = os.path.realpath(sys.modules[module_name].__file__) == os.path.realpath(requested_file)
        if not same_file:
            del sys.modules[module_name]


@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)
