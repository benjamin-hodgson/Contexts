import re
import types
import inspect
from . import errors


establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Gg]iven|[Ss]et_?[Uu]p)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup|[Tt]ear_?[Dd]own)")
spec_re = re.compile(r"([Ss]pec|[Ww]hen)")
module_re = re.compile(r"([Ss]pec|[Tt]est)")


def get_contexts_from_module(module):
    contexts = []
    contexts.extend(get_classes_from_module(module))
    for sub_module in get_modules_from_package(module):
        contexts.extend(get_contexts_from_module(sub_module))
    return contexts


def get_classes_from_module(module):
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if re.search(spec_re, name):
            yield cls()


def get_modules_from_package(package):
    for name, module in inspect.getmembers(package, inspect.ismodule):
        if re.search(module_re, name):
            yield module


def find_setups(spec):
    return find_methods_matching(spec, establish_re, top_down=True, one_per_class=True)


def find_actions(spec):
    return find_methods_matching(spec, because_re, one_only=True, one_per_class=True)


def find_assertions(spec):
    return find_methods_matching(spec, should_re)


def find_teardowns(spec):
    return find_methods_matching(spec, cleanup_re, one_per_class=True)


def find_methods_matching(spec, regex, *, top_down=False, one_only=False, one_per_class=False):
    found = []
    mro = spec.__class__.__mro__
    classes = reversed(mro) if top_down else mro
    for cls in classes:
        found.extend(find_methods_on_class_matching(cls, spec, regex, one_only or one_per_class))
        if one_only and found:
            break
    return found


def find_methods_on_class_matching(cls, instance, regex, one_per_class):
    found = []
    for name, func in cls.__dict__.items():
        if re.search(regex, name) and callable(func):
            method = types.MethodType(func, instance)
            found.append(method)

    if one_per_class:
        assert_single_method_of_given_type(cls, found)

    return found


def assert_single_method_of_given_type(cls, found):
    if len(found) > 1:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += ", ".join([meth.__func__.__name__ for meth in found])
        raise errors.TooManySpecialMethodsError(msg)
