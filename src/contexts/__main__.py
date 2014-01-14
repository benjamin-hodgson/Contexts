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


def parse_args(args):
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

    args = parser.parse_args(args)

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
    plugin_list = []

    if args.rewriting:
        plugin_list.append(AssertionRewritingImporter())
    else:
        plugin_list.append(Importer())

    if args.shuffle:
        plugin_list.append(Shuffler())

    plugin_list.extend(create_reporting_plugins(args))

    plugin_list.append(ExitCodeReporter())

    return plugin_list


def create_reporting_plugins(args):
    plugin_list = []

    if args.teamcity:
        plugin_list.append(plugins.teamcity.TeamCityReporter(sys.stdout))
        return plugin_list

    if args.verbosity == 'quiet':
        plugin_list.append(plugins.cli.StdOutCapturingReporter(StringIO()))
        return plugin_list

    if args.verbosity == 'normal':
        plugin_list.append(plugins.cli.DotsReporter(sys.stdout))

    if args.colour and args.capture and args.verbosity == 'verbose':
        plugin_list.append(plugins.cli.ColouringDecorator(plugins.cli.StdOutCapturingReporter)(sys.stdout))

    elif args.colour and not args.capture and args.verbosity == 'verbose':
        plugin_list.append(plugins.cli.ColouringDecorator(plugins.cli.VerboseReporter)(sys.stdout))

    elif args.capture and not args.colour and args.verbosity == 'verbose':
        plugin_list.append(plugins.cli.StdOutCapturingReporter(sys.stdout))

    elif not args.colour and not args.capture and args.verbosity == 'verbose':
        plugin_list.append(plugins.cli.VerboseReporter(sys.stdout))

    elif args.capture and args.colour and args.verbosity == 'normal':
        plugin_list.append(plugins.cli.FailureOnlyDecorator(plugins.cli.ColouringDecorator(plugins.cli.StdOutCapturingReporter))(sys.stdout))

    elif args.capture and not args.colour and args.verbosity == 'normal':
        plugin_list.append(plugins.cli.FailureOnlyDecorator(plugins.cli.StdOutCapturingReporter)(sys.stdout))

    elif args.colour and not args.capture and args.verbosity == 'normal':
        plugin_list.append(plugins.cli.FailureOnlyDecorator(plugins.cli.ColouringDecorator(plugins.cli.VerboseReporter))(sys.stdout))

    elif not args.colour and not args.capture and args.verbosity == 'normal':
        plugin_list.append(plugins.cli.FailureOnlyDecorator(plugins.cli.VerboseReporter)(sys.stdout))

    if args.verbosity != 'quiet':
        plugin_list.append(plugins.cli.FinalCountsReporter(sys.stdout))
        plugin_list.append(plugins.cli.TimedReporter(sys.stdout))

    return plugin_list


if __name__ == "__main__":
	cmd()
