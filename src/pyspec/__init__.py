import sys
from .builders import build_suite
from .runners import run_main_module


def run(spec=None):
    if spec is None:
        return run_main_module()

    suite = build_suite(spec)
    suite.run()
    return suite.result


def main():
    result = run_main_module()

    if result.failures or result.errors:
        sys.exit(1)
    sys.exit(0)


def catch(func):
    try:
        func()
    except Exception as e:
        return e
