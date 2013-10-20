import contextlib
import glob
import importlib
import os
import re
import sys


module_re = re.compile(r"([Ss]pec|[Tt]est)")


def import_modules_in_directory(dir_path):
    if os.path.join(dir_path, "__init__.py") in glob.glob(os.path.join(dir_path, '*.py')):
        imported_modules = []
        imported_modules.append(import_module_from_file(dir_path))
        for file_path in glob.iglob(os.path.join(dir_path, '*.py')):
            if "__init__.py" in file_path:
                continue
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            package_name = os.path.basename(dir_path)
            imported_modules.append(import_module(os.path.dirname(dir_path), package_name + '.' + module_name))
        return imported_modules

    imported_modules = []
    for file_path in glob.iglob(os.path.join(dir_path, '*.py')):
        if re.search(module_re, os.path.basename(file_path)):
            imported_modules.append(import_module_from_file(file_path))
    return imported_modules


def import_module(dir_path, module_name):
    with prepend_folder_to_sys_dot_path(dir_path):
        return importlib.import_module(module_name)


def import_module_from_file(file_path):
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return import_module(folder, module_name)


@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)
