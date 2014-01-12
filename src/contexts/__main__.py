import argparse
import os
import sys
from io import StringIO
from . import main
from . import plugins
from .plugins.other import Shuffler


def cmd():
    args = parse_args(sys.argv[1:])
    reporters = create_reporters(args)
    if args.shuffle:
        reporters.insert(0, Shuffler())
    main(os.path.realpath(args.path), reporters, args.rewriting)


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

    return parser.parse_args(args)


def create_reporters(args):
    # Refactoring hint:
    # multiple inheritance is part of the reason this function is hard to test.
    # Try to get the reporters to the point where they can be composed
    # without inheritance.
    if not sys.stdout.isatty():
        args.colour = False

    try:
        import colorama
    except ImportError:
        args.colour = False
    else:
        colorama.init()

    if args.teamcity or "TEAMCITY_VERSION" in os.environ:
        return [plugins.teamcity.TeamCityReporter(sys.stdout)]

    if args.verbosity == 'quiet':
        return [plugins.cli.StdOutCapturingReporter(StringIO())]

    if args.verbosity == 'verbose':
        if not args.capture:
            if args.colour:
                return [plugins.cli.ColouredVerboseReporter(sys.stdout), plugins.cli.TimedReporter(sys.stdout)]
            return [plugins.cli.VerboseReporter(sys.stdout), plugins.cli.TimedReporter(sys.stdout)]
        if args.colour:
            return [plugins.cli.ColouredVerboseCapturingReporter(sys.stdout), plugins.cli.TimedReporter(sys.stdout)]
        return [plugins.cli.StdOutCapturingReporter(sys.stdout), plugins.cli.TimedReporter(sys.stdout)]

    if args.capture:
        if args.colour:
            return [
                plugins.cli.DotsReporter(sys.stdout),
                plugins.cli.ColouredSummarisingCapturingReporter(sys.stdout),
                plugins.cli.TimedReporter(sys.stdout)
            ]
        return [
            plugins.cli.DotsReporter(sys.stdout),
            plugins.cli.SummarisingCapturingReporter(sys.stdout),
            plugins.cli.TimedReporter(sys.stdout)
        ]

    if not args.capture:
        if args.colour:
            return [
                plugins.cli.DotsReporter(sys.stdout),
                plugins.cli.ColouredSummarisingReporter(sys.stdout),
                plugins.cli.TimedReporter(sys.stdout)
            ]
        return [
            plugins.cli.DotsReporter(sys.stdout),
            plugins.cli.SummarisingReporter(sys.stdout),
            plugins.cli.TimedReporter(sys.stdout)
        ]


if __name__ == "__main__":
	cmd()
