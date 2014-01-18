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
    plugin_list = create_plugins(args)
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


def create_plugins(args):
    plugin_list = [create_importing_plugin(args)]

    if args.shuffle:
        plugin_list.append(Shuffler())

    plugin_list.extend(create_reporting_plugins(args))
    plugin_list.append(ExitCodeReporter())

    return plugin_list

def create_importing_plugin(args):
    if args.rewriting:
        return AssertionRewritingImporter()
    else:
        return Importer()

def create_reporting_plugins(args):
    if args.teamcity:
        return [plugins.teamcity.TeamCityReporter(sys.stdout)]

    if args.verbosity == 'quiet':
        return [plugins.cli.StdOutCapturingReporter(StringIO())]

    inner_plugin_cls = get_inner_plugin(args)
    maybe_coloured_cls = apply_colouring(args, inner_plugin_cls)
    maybe_muted_cls = apply_success_muting(args, maybe_coloured_cls)

    plugin_list = [
        maybe_muted_cls(sys.stdout),
        plugins.cli.FinalCountsReporter(sys.stdout),
        plugins.cli.TimedReporter(sys.stdout)
    ]

    if args.verbosity == 'normal':
        plugin_list.insert(0, plugins.cli.DotsReporter(sys.stdout))

    return plugin_list

def get_inner_plugin(args):
    if args.capture:
        return plugins.cli.StdOutCapturingReporter
    return plugins.cli.VerboseReporter

def apply_colouring(args, inner_plugin_cls):
    if args.colour:
        return plugins.cli.ColouringDecorator(inner_plugin_cls)
    return inner_plugin_cls

def apply_success_muting(args, maybe_coloured_cls):
    if args.verbosity == 'normal':
        return plugins.cli.FailureOnlyDecorator(maybe_coloured_cls)
    return maybe_coloured_cls


if __name__ == "__main__":
	cmd()
