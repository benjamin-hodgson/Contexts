import itertools
from . import errors


def build_assertion_name(func):
    module_name = func.__module__
    method_name = func.__qualname__
    return '{}.{}'.format(module_name, method_name)


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
