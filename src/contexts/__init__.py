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
        result = reporting.TimedCapturingTextResult()
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
    result = run(os.getcwd())
    if not result:
        sys.exit(1)
    sys.exit(0)
