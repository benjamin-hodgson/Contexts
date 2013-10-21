import contextlib
import importlib
import os
import sys
from . import finders


###########################################################
# 'Importer' functions - call finders and loaders
###########################################################

def import_from_directory(dir_path):
    finder = finders.ModuleFinder(dir_path)
    module_specs = finder.find_modules()
    return (load_module(*spec) for spec in module_specs)


###########################################################
# 'Loader' functions - import modules
###########################################################

def load_module(dir_path, module_name):
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


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
