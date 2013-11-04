import os
from . import module_finders
from .importers import load_module

def import_from_directory(dir_path):
    module_specs = module_finders.find_modules(dir_path)
    return (load_module(*spec) for spec in module_specs)


def import_from_file(file_path):
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return load_module(folder, module_name)
