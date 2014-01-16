import argparse
import os
import sys
from io import StringIO
from . import main
from . import plugins
from .plugins.shared import ExitCodeReporter
from .plugins.shuffling import Shuffler
from .plugins.importing import Importer
from .plugins.assertion_rewriting import AssertionRewritingImporter


def cmd():
    args = parse_args(sys.argv[1:])
    plugin_list = Configuration(args).create_plugins()
    main(os.path.realpath(args.path), plugin_list)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--no-capture',
        action='store_false',
        dest='capture',
        default=True,
        help="Disable capturing of stdout during tests.")
    parser.add_argument('--teamcity',
        action='store_true',
        dest='teamcity',
        default=False,
        help="Enable teamcity test reporting.")
    parser.add_argument('--no-random',
        action='store_false',
        dest='shuffle',
        default=True,
        help="Disable test order randomisation.")
    parser.add_argument('--no-colour',
        action='store_false',
        dest='colour',
        default=True,
        help='Disable coloured output.')
    parser.add_argument('--no-assert',
        action='store_false',
        dest='rewriting',
        default=True,
        help='Disable assertion rewriting.')
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (default current directory)")

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-v', '--verbose',
        action='store_const',
        dest='verbosity',
        const='verbose',
        default='normal',
        help="Enable verbose progress reporting.")
    group.add_argument('-q', '--quiet',
        action='store_const',
        dest='verbosity',
        const='quiet',
        default='normal',
        help="Disable progress reporting.")

    args = parser.parse_args(argv)

    if "TEAMCITY_VERSION" in os.environ:
        args.teamcity = True

    if not sys.stdout.isatty():
        args.colour = False

    if args.colour:
        try:
            import colorama
        except ImportError:
            args.colour = False
        else:
            colorama.init()

    return args


class Configuration(object):
    def __init__(self, args):
        self.args = args

    def __getattr__(self, name):
        return getattr(self.args, name)

    def create_plugins(self):
        plugin_list = [self.create_importing_plugin()]
        if self.shuffle:
            plugin_list.append(Shuffler())

        plugin_list.extend(self.create_reporting_plugins())
        plugin_list.append(ExitCodeReporter())

        return plugin_list

    def create_importing_plugin(self):
        if self.rewriting:
            return AssertionRewritingImporter()
        else:
            return Importer()

    def create_reporting_plugins(self):
        if self.teamcity:
            return [plugins.teamcity.TeamCityReporter(sys.stdout)]

        if self.verbosity == 'quiet':
            return [plugins.cli.StdOutCapturingReporter(StringIO())]

        inner_plugin_cls = self.get_inner_plugin()
        maybe_coloured_cls = self.apply_colouring(inner_plugin_cls)
        maybe_muted_cls = self.apply_failure_muting(maybe_coloured_cls)

        plugin_list = [
            maybe_muted_cls(sys.stdout),
            plugins.cli.FinalCountsReporter(sys.stdout),
            plugins.cli.TimedReporter(sys.stdout)
        ]

        if self.verbosity == 'normal':
            plugin_list.insert(0, plugins.cli.DotsReporter(sys.stdout))

        return plugin_list

    def get_inner_plugin(self):
        if self.capture:
            return plugins.cli.StdOutCapturingReporter
        return plugins.cli.VerboseReporter

    def apply_colouring(self, inner_plugin_cls):
        if self.colour:
            return plugins.cli.ColouringDecorator(inner_plugin_cls)
        return inner_plugin_cls

    def apply_failure_muting(self, maybe_coloured_cls):
        if self.verbosity == 'normal':
            return plugins.cli.FailureOnlyDecorator(maybe_coloured_cls)
        return maybe_coloured_cls





if __name__ == "__main__":
	cmd()
