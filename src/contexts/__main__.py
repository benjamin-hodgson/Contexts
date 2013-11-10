import argparse
import os
import sys
from . import _run_impl
from . import reporting


def cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--no-capture',
    	action='store_const',
    	dest='reporter',
    	const=reporting.NonCapturingCLIReporter(),
    	default=reporting.CapturingCLIReporter())
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd())
    args = parser.parse_args()

    _run_impl(os.path.realpath(args.path), args.reporter)

    if args.reporter.failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
	cmd()
