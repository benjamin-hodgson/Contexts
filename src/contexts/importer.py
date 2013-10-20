import contextlib
import glob
import importlib
import os
import sys
from . import finders


###########################################################
# 'Importer' functions - call finders and loaders
###########################################################

def import_modules_in_directory(dir_path):
    if os.path.join(dir_path, "__init__.py") in glob.glob(os.path.join(dir_path, '*.py')):
        return import_modules_in_package(dir_path)

    found_filenames = finders.find_modules_in_directory(dir_path)
    return [load_module_from_file(f) for f in found_filenames]


def import_modules_in_package(package_directory):
    parent_folder = os.path.dirname(package_directory)
    found_module_names = finders.find_modules_in_package(package_directory)
    return [load_package(package_directory)] + [load_module(parent_folder, n) for n in found_module_names]


###########################################################
# 'Loader' functions - import modules
###########################################################

def load_module(dir_path, module_name):
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


def load_package(dir_path):
    return load_module_from_file(dir_path)


def load_module_from_file(file_path):
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return load_module(folder, module_name)


###########################################################
# Utility functions
###########################################################

@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)
