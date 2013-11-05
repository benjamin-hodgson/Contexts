import argparse
import os
import sys
from . import _run_impl
from . import reporting


def cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--no-capture',
    	action='store_const',
    	dest='result',
    	const=reporting.NonCapturingCLIResult(),
    	default=reporting.CapturingCLIResult())
    args = parser.parse_args()

    _run_impl(os.getcwd(), args.result)
    
    if args.result.failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
	cmd()
