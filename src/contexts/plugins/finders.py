import inspect
import re
from .. import errors


establish_re = re.compile(r"[Ee]stablish|[Cc]ontext|[Gg]iven")
because_re = re.compile(r"[Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter")
should_re = re.compile(r"[Ss]hould|(^[Ii]|[a-z]I|_i)t|[Mm]ust|[Ww]ill|[Tt]hen")
cleanup_re = re.compile(r"[Cc]leanup")


class NameBasedFinder(object):
    def get_setup_methods(self, spec_cls):
        found = []

        for cls in reversed(inspect.getmro(spec_cls)):
            found_on_class = []
            for name, val in cls.__dict__.items():
                if callable(val) and name_matches(name, establish_re):
                    found_on_class.append(val)

            assert_one_method(found_on_class, cls)
            found.extend(found_on_class)

        return found

    def get_action_method(self, cls):
        found = []
        for name, val in cls.__dict__.items():
            if callable(val) and name_matches(name, because_re):
                found.append(val)

        assert_one_method(found, cls)
        return found[0] if found else None

    def get_assertion_methods(self, cls):
        found = []
        for name, val in cls.__dict__.items():
            if callable(val) and name_matches(name, should_re):
                found.append(val)
        return found


def name_matches(name, regex):
    all_regexes = {establish_re, because_re, should_re, cleanup_re}
    all_regexes.remove(regex)

    if regex.search(name):
        if any(r.search(name) for r in all_regexes):
            raise errors.MethodNamingError("The method {} is ambiguously named".format(name))
        return True
    return False


def assert_one_method(found_methods, cls):
    if len(found_methods) > 1:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += ", ".join([func.__name__ for func in found_methods])
        raise errors.TooManySpecialMethodsError(msg)
