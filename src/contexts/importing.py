import contextlib
import importlib
import os
import sys


def import_from_file(file_path):
    """
    Import the specified file, with an unqualified module name.
    """
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return import_module(folder, module_name)


def import_module(dir_path, module_name):
    """
    Load specified module from the specified directory
    """
    prune_sys_dot_modules(dir_path, module_name)
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


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
