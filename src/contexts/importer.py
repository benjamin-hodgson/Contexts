import contextlib
import importlib
import os
import sys
from . import finders


###########################################################
# 'Importer' functions - call finders and loaders
###########################################################

def import_modules_in_directory(dir_path):
    finder = finders.ModuleFinder(dir_path)
    parent_folder, found_module_names = finder.find_modules()
    return (load_module(parent_folder, n) for n in found_module_names)


###########################################################
# 'Loader' functions - import modules
###########################################################

def load_module(dir_path, module_name):
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


def load_package(dir_path):
    parent_folder = os.path.dirname(dir_path)
    filename = os.path.basename(dir_path)
    module_name = os.path.splitext(filename)[0]
    return load_module(parent_folder, module_name)


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
