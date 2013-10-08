import re
import types
import inspect


establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Ss]et_?[Uu]p)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup|[Tt]ear_?[Dd]own)")
spec_re = re.compile(r"(^|_)([Ss]pec|[Ww]hen)")


def get_contexts_from_module(module):
    contexts = []
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if re.search(spec_re, name):
            contexts.append(cls())
    return contexts


def find_methods_matching(spec, regex, *, top_down=False, one_only=False):
    ret = []
    mro = spec.__class__.__mro__
    classes = reversed(mro) if top_down else mro
    for cls in classes:
        for func in find_methods_on_class_matching(cls, regex):
            method = types.MethodType(func, spec)
            ret.append(method)
            if one_only:
                return ret
    return ret

def find_methods_on_class_matching(cls, regex):
    for name, func in cls.__dict__.items():
        if re.search(regex, name) and callable(func):
            yield func
