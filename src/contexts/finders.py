import inspect
import re


class_re = re.compile(r"([Ss]pec|[Ww]hen)")


def find_specs_in_module(module):
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if hasattr(cls, '_contexts_role'):
            name = cls._contexts_role
        if class_re.search(name):
            yield cls
