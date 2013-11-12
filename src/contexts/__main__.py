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
    	default=True)
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd())
    parser.add_argument('--teamcity',
        action='store_true',
        dest='teamcity',
        default=False)
    args = parser.parse_args()

    if args.teamcity:
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
