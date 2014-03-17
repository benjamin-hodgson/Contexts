import os
from collections import namedtuple
from .plugin_interface import TEST_FILE


PackageSpecification = namedtuple('PackageSpecification', ['parent_folder', 'package_name'])
ModuleSpecification = namedtuple('ModuleSpecification', ['parent_folder', 'module_name'])


def create_importer(folder, plugin_composite, exception_handler):
    if ispackage(folder):
        return PackageModuleImporter(folder, plugin_composite, exception_handler)
    else:
        return FolderModuleImporter(folder, plugin_composite, exception_handler)


class Importer(object):
    def get_file_details(self):
        specs = []
        for filename in os.listdir(self.directory):
            full_path = os.path.realpath(os.path.join(self.directory, filename))
            if not os.path.isfile(full_path) or filename == '__init__.py':
                continue
            if self.plugin_composite.identify_file(full_path) is TEST_FILE:
                module_name = self.module_prefix + remove_extension(filename)
                specs.append(ModuleSpecification(self.location, module_name))
        return specs


class FolderModuleImporter(Importer):
    def __init__(self, directory, plugin_composite, exception_handler):
        self.directory = directory
        self.location = self.directory
        self.module_prefix = ''
        self.plugin_composite = plugin_composite
        self.exception_handler = exception_handler

    def module_specs(self):
        return self.get_file_details()

    def import_file(self, filename):
        module_name = os.path.splitext(filename)[0]
        with self.exception_handler.importing(self.directory, module_name):
            return self.plugin_composite.import_module(self.directory, module_name)


class PackageModuleImporter(Importer):
    def __init__(self, directory, plugin_composite, exception_handler):
        directory = os.path.realpath(directory)
        self.package_spec = get_package_specification(directory)

        self.directory = directory
        self.location = self.package_spec[0]
        self.module_prefix = self.package_spec[1] + '.'
        self.plugin_composite = plugin_composite
        self.exception_handler = exception_handler

    def module_specs(self):
        return get_parent_package_specs(*self.package_spec) + self.get_file_details()

    def import_file(self, filename):
        module_list = ModuleList(self.plugin_composite, self.exception_handler)
        top_folder, package_name = self.package_spec
        add_parent_packages_to_list(module_list, top_folder, package_name)
        if filename != '__init__.py':
            module_name = package_name + '.' + os.path.splitext(filename)[0]
            module_list.add(top_folder, module_name)
        return module_list.modules[-1]


def add_parent_packages_to_list(module_list, top_folder, package_name):
    for top_folder, full_name in get_parent_package_specs(top_folder, package_name):
        module_list.add(top_folder, full_name)


def get_parent_package_specs(top_folder, package_name):
    parent_package_specs = []

    i = 1
    while i <= len(package_name.split('.')):
        spec = PackageSpecification(top_folder, '.'.join(package_name.split('.')[:i]))
        parent_package_specs.append(spec)
        i += 1

    return parent_package_specs


# FIXME: i don't think it's right for ModuleList to exist. TestRun is a list of
# modules ('Suites') so we dont need another list of modules.
# however i also feel weird about the two alternatves: initialising TestRun with an empty
# list of modules and then populating it inside run(), or importing the modules in the constructor
# So, until i come up with a better idea, this class lives on and will only be used inside import_file()
class ModuleList(object):
    def __init__(self, plugin_composite, exception_handler):
        self.modules = []
        self.plugin_composite = plugin_composite
        self.exception_handler = exception_handler
    def add(self, folder, module_name):
        with self.exception_handler.importing(folder, module_name):
            module = self.plugin_composite.import_module(folder, module_name)
            self.modules.append(module)


def get_package_specification(directory):
    current_parent = os.path.dirname(directory)
    package_names = [os.path.basename(directory)]

    while ispackage(current_parent):
        dirpath, current_parent = current_parent, os.path.dirname(current_parent)
        package_names.append(os.path.basename(dirpath))

    full_package_name = '.'.join(reversed(package_names))
    return PackageSpecification(current_parent, full_package_name)


def ispackage(directory):
    return "__init__.py" in os.listdir(directory)


def remove_extension(filename):
    name, extension = os.path.splitext(filename)
    return name
