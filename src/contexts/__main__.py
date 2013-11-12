import argparse
import os
import sys
from . import _run_impl
from . import reporting


def cmd():
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
        help="Enable teamcity test reporting")
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run")
    args = parser.parse_args()

    if args.teamcity or "TEAMCITY_VERSION" in os.environ:
        reporter = reporting.TeamCityReporter()
    elif args.capture:
        reporter = reporting.CapturingCLIReporter()
    else:
        reporter = reporting.NonCapturingCLIReporter()

    _run_impl(os.path.realpath(args.path), reporter)

    if reporter.failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
	cmd()
