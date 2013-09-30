import collections
from .core import Context, Result


def run(*specs):
    result = Result()

    for spec in specs:
        if isinstance(spec, collections.Iterable):
            # will fail if we're passed very deeply nested lists of specs
            # though that won't happen
            result += run(*spec)
        else:
            result += Context(spec).run()

    return result
