import argparse
import os
import sys
from . import run
from . import reporting

import colorama; colorama.init()


def cmd():
    args = parse_args(sys.argv[1:])

    reporters = create_reporters(args)

    passed = run(os.path.realpath(args.path), reporters, args.shuffle)

    if not passed:
        sys.exit(1)
    sys.exit(0)


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--no-capture',
        action='store_false',
        dest='capture',
        default=True,
        help="Disable capturing of stdout during tests.")
    parser.add_argument('-v', '--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help="Enable verbose progress reporting.")
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
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (default current directory)")
    return parser.parse_args(args)


def create_reporters(args):
    if args.teamcity or "TEAMCITY_VERSION" in os.environ:
        return (reporting.teamcity.TeamCityReporter(sys.stdout),)
    elif args.verbose:
        return (reporting.cli.ColouredReporter(sys.stdout),)
    elif args.capture:
        return (
            reporting.cli.DotsReporter(sys.stdout),
            type("ColouredCapturingReporter", (reporting.cli.ColouredReporter, reporting.cli.StdOutCapturingReporter), {})(sys.stdout),
            reporting.cli.TimedReporter(sys.stdout)
        )
    return (
        reporting.cli.DotsReporter(sys.stdout),
        type("ColouredCapturingReporter", (reporting.cli.ColouredReporter, reporting.cli.SummarisingReporter), {})(sys.stdout),
        reporting.cli.TimedReporter(sys.stdout)
    )


if __name__ == "__main__":
	cmd()
