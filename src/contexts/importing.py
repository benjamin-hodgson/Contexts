import os


class Importer:
    def __init__(self, plugin_notifier):
        self.plugin_notifier = plugin_notifier

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
        return self.plugin_notifier.call_plugins('import_module', dir_path, module_name)
