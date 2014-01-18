import inspect
import re
from .. import errors


establish_re = re.compile(r"[Ee]stablish|[Cc]ontext|[Gg]iven")
because_re = re.compile(r"[Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter")
should_re = re.compile(r"[Ss]hould")
cleanup_re = re.compile(r"[Cc]leanup")


class NameBasedFinder(object):
    def get_setup_methods(self, spec_cls):
        found = []

        for cls in reversed(inspect.getmro(spec_cls)):
            found_on_class = []
            for name, val in cls.__dict__.items():
                if not callable(val):
                    continue

                if establish_re.search(name):
                    if because_re.search(name) or should_re.search(name) or cleanup_re.search(name):
                        raise errors.MethodNamingError("The method {} is ambiguously named".format(name))

                    found_on_class.append(val)

            if len(found_on_class) > 1:
                msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
                msg += ", ".join([func.__name__ for func in found])
                raise errors.TooManySpecialMethodsError(msg)

            found.extend(found_on_class)

        return found

    def get_action_method(self, cls):
        found = []
        for name, val in cls.__dict__.items():
            if not callable(val):
                continue

            if because_re.search(name):
                if establish_re.search(name) or should_re.search(name) or cleanup_re.search(name):
                    raise errors.MethodNamingError("The method {} is ambiguously named".format(name))

                found.append(val)

        if len(found) > 1:
            msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
            msg += ", ".join([func.__name__ for func in found])
            raise errors.TooManySpecialMethodsError(msg)

        return found[0] if len(found) == 1 else None
