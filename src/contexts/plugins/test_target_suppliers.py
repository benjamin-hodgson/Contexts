import os
from contextlib import contextmanager

# such a hack :(
from ..discovery import create_importer
from .importing import Importer


class CommandLineSupplier(object):
    def setup_parser(self, parser):
        parser.add_argument('path',
            action='store',
            nargs='?',
            default=os.getcwd(),
            help="Path to the test file or directory to run. (Default: current directory)")

    def initialise(self, args, env):
        drive, path = os.path.splitdrive(args.path)  # the path may begin with, eg, "C:/"
        if ':' in path:
            path, _, classname = args.path.rpartition(':')
        else:
            path, classname = args.path, ''

        path = os.path.realpath(path)

        if not os.path.isfile(path) and not os.path.isdir(path):
            raise ValueError("File or folder not found: {}".format(path))

        # i feel awful about this
        if classname:
            plugin = Importer()
            plugin.identify_file = lambda x: x == path
            exception_handler = HackyExceptionHandler()

            folder, filename = os.path.split(path)

            importer = create_importer(folder, plugin, exception_handler)
            module = importer.import_file(filename)
            self.to_run = getattr(module, classname)
        else:
            self.to_run = path
        return True

    def get_object_to_run(self):
        return self.to_run

    def __eq__(self, other):
        return type(self) == type(other)


# this plugin is unusual because there is no need to load it from an entry point
# so no initialise method
class ObjectSupplier(object):
    def __init__(self, to_run):
        self.to_run = to_run
    def get_object_to_run(self):
        return self.to_run


class HackyExceptionHandler:
    @contextmanager
    def importing(self, *args, **kwargs):
        yield
