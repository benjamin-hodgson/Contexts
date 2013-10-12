import sys
from .runners import run


__all__ = ['run', 'main', 'catch']


def main():
    result = run(sys.modules["__main__"])
    print(result.format_result())

    if result.failed:
        sys.exit(1)
    sys.exit(0)


def catch(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        return e
