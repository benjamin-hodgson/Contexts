import os


class TestObjectSupplier(object):
    def setup_parser(self, parser):
        parser.add_argument('path',
            action='store',
            nargs='?',
            default=os.getcwd(),
            help="Path to the test file or directory to run. (Default: current directory)")

    def initialise(self, args, env):
        self.to_run = args.path
        return True

    def get_object_to_run(self):
        return self.to_run

    def __eq__(self, other):
        return type(self) == type(other)
