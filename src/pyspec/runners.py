import sys
from .reporting import format_result
from .builders import build_suite


def run_main_module():
    result = run_module(sys.modules["__main__"])
    print(format_result(result))
    return result


def run_module(module):
    suite = build_suite(module)
    suite.run()
    return suite.result
