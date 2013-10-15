import contextlib
import importlib
import os
import sys


def import_module_from_filename(file_path):
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]

    with prepend_folder_to_sys_dot_path(folder):
        module = importlib.import_module(module_name)
    
    return module


@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)
