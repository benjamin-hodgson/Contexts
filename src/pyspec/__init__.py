from .core import Result
from .builder import build_suite


def run(*specs):
    result = Result()

    for spec in specs:
        suite = build_suite(spec)
        suite.run()
        result += suite.result

    return result


