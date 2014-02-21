import os


class PathSupplier(object):
    def setup_parser(self, parser):
        parser.add_argument('path',
            action='store',
            nargs='?',
            default=os.getcwd(),
            help="Path to the test file or directory to run. (Default: current directory)")

    def initialise(self, args, env):
        path = os.path.realpath(args.path)

        if not os.path.isfile(path) and not os.path.isdir(path):
            raise ValueError("You have to supply a real path")

        self.to_run = args.path
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
