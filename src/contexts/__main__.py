import argparse
import os
import sys
from . import _run_impl
from .reporting import cli, teamcity


def cmd():
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
        help="Path to the test file or directory to run.")
    args = parser.parse_args()

    if args.teamcity or "TEAMCITY_VERSION" in os.environ:
        reporter = teamcity.TeamCityReporter()
    elif args.verbose:
        reporter = cli.VerboseReporter()
    elif args.capture:
        reporter = type(
            "CapturingCLIReporter",
            (cli.DotsReporter, cli.TimedReporter, cli.StdOutCapturingReporter),
            {})()
    else:
        reporter = type(
            "NonCapturingCLIReporter",
            (cli.DotsReporter, cli.TimedReporter, cli.SummarisingReporter),
            {})()

    _run_impl(os.path.realpath(args.path), reporter, args.shuffle)

    if reporter.failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
	cmd()
