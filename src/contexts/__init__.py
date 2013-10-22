import sys
from . import builders
from . import reporting


__all__ = ['run', 'main', 'catch']


def main():
    passed = run()
    if not passed:
        sys.exit(1)
    sys.exit(0)


def run(spec=None, result=None):
    if result is None:
        result = reporting.TimedTextResult()
    if spec is None:
        spec = sys.modules['__main__']

    suite = builders.build_suite(spec)
    suite.run(result)
    result.summarise()

    return not result.failed

def catch(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        return e
