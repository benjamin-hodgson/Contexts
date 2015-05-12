import shlex
import sys


class ArgvForwarder(object):
    def setup_parser(self, parser):
        parser.add_argument("--argv", dest="argv", type=str)

    def initialise(self, args, environ):
        if args.argv:
            self.real_argv = sys.argv.copy()
            self.argv_override = shlex.split(args.argv)
            return True
        return False

    def test_run_started(self):
        sys.argv[1:] = self.argv_override

    def test_run_ended(self):
        sys.argv = self.real_argv
