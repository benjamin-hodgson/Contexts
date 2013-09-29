import collections
from .core import Spec, SpecSuite, Result


def run(*specs):
    result = Result()

    for spec in specs:
        if isinstance(spec, collections.Iterable):
            result += SpecSuite(spec).run()
        else:
            result += Spec(spec).run()

    return result
