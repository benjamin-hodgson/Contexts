import sys
from .runners import run
from .reporting import TextResult


__all__ = ['run', 'main', 'catch']


def main():
    result = TextResult()
    run(sys.modules["__main__"], result)
    result.print_summary()

    if result.failed:
        sys.exit(1)
    sys.exit(0)


def catch(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        return e
