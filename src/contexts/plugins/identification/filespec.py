import io
import os
from pathlib import PurePath
from contexts.plugin_interface import TEST_FOLDER, TEST_FILE


class FileSpecIdentifier:

    def __init__(self):
        self._specs = None

    def setup_parser(self, parser):
        parser.add_argument(
            '--specs',
            action='store',
            dest='specs',
            default=None,
            help="Path to a file containing files and directories to search for tests.")

    def initialise(self, args=None, env=None, file=None, cwd=None):
        """
        Filthy hack: we provide file and cwd here rather than as constructor
        args because Mr Hodgson decided to pass stdout as the only parameter
        to __init__.
        File should only be passed during tests.
        """
        self.spec_file = args and args.specs or None
        self.cwd = cwd or os.getcwd()
        self.file = file
        return self.spec_file is not None

    def identify_folder(self, folder):
        folder = PurePath(folder)
        for f in self.specs:
            if f == folder:
                return TEST_FOLDER
            if(folder in f.parents):
                return TEST_FOLDER

    def identify_file(self, file):
        file = PurePath(file)
        for f in self.specs:
            if(f == file):
                return TEST_FILE

    @property
    def specs(self):
        if(self._specs is None):
            self.read_from_file()
        return self._specs

    def get_path(self, p):
        return PurePath(self.cwd, p.rstrip())

    def read_from_file(self):
        if(self.file is not None):
            self._specs = [PurePath(self.cwd, p) for p in self.file.readlines()]
        else:
            with io.open(self.spec_file, 'r') as file:
                self._specs = [self.get_path(p) for p in file.readlines()]
