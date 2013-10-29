import argparse
import os
import sys
from . import builders
from . import reporting
from . import core


__all__ = ['run', 'main', 'catch']


def main():
    passed = run()
    if not passed:
        sys.exit(1)
    sys.exit(0)


def run(spec=None, result=None):
    if result is None:
        result = reporting.CapturingDefaultResult()
    if spec is None:
        spec = sys.modules['__main__']

    _run_impl(spec, result)

    return not result.failed


def _run_impl(spec, result):
    result_runner = core.ResultRunner(result)
    suite = builders.build_suite(spec)
    suite.run(result_runner)


def catch(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        return e


def cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--no-capture', action='store_const', dest='result', const=reporting.NonCapturingCLIResult(), default=reporting.CLIResult())
    args = parser.parse_args()

    result = run(os.getcwd(), args.result)
    if not result:
        sys.exit(1)
    sys.exit(0)
