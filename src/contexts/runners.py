import sys
from .builders import build_suite
from .reporting import TextResult


def run(spec=None, result=None):
    if result is None:
        result = TextResult()
    if spec is None:
        spec = sys.modules['__main__']
    suite = build_suite(spec)
    suite.run(result)

    return not result.failed
