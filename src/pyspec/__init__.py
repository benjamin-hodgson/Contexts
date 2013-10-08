import sys
from .reporting import format_result
from .core import Result
from .builders import build_suite


def run(*specs):
    if not specs:
        return run_main_module()

    result = Result()

    for spec in specs:
        suite = build_suite(spec)
        suite.run()
        result += suite.result

    return result


def main():
    result = run_main_module()

    if result.failures or result.errors:
        sys.exit(1)
    sys.exit(0)


def run_main_module():
    result = run(sys.modules["__main__"])
    print(format_result(result))
    return result
