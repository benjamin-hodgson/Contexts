import re
from . import Plugin, CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from .. import errors


class_re = re.compile(r"[Ss]pec|[Ww]hen")
example_re = re.compile(r"[Ee]xample|[Dd]ata")
establish_re = re.compile(r"[Ee]stablish|[Cc]ontext|[Gg]iven")
because_re = re.compile(r"[Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter")
should_re = re.compile(r"[Ss]hould|((^|[a-z]|_)I|(^|_)i)t|[Mm]ust|[Ww]ill|[Tt]hen")
cleanup_re = re.compile(r"[Cc]leanup")


class NameBasedIdentifier(object):
    def identify_class(self, cls):
        if class_re.search(cls.__name__):
            return CONTEXT

    def identify_method(self, method):
        d = {
            example_re: EXAMPLES,
            establish_re: SETUP,
            because_re: ACTION,
            should_re: ASSERTION,
            cleanup_re: TEARDOWN
        }
        name = method.__name__

        for regex in d:
            if regex.search(name):
                assert_not_ambiguous(name, regex)
                return d[regex]

    def __eq__(self, other):
        return type(self) == type(other)


def assert_not_ambiguous(name, regex):
    all_regexes = {example_re, establish_re, because_re, should_re, cleanup_re}
    all_regexes.remove(regex)

    if any(r.search(name) for r in all_regexes):
        msg = "The method {} is ambiguously named".format(name)
        raise errors.MethodNamingError(msg)


class DecoratorBasedIdentifier(object):
    def identify_method(self, method):
        if not hasattr(method, "_contexts_role"):
            return None

        d = {
            "examples": EXAMPLES,
            "establish": SETUP,
            "because": ACTION,
            "should": ASSERTION,
            "cleanup": TEARDOWN
        }
        return d[method._contexts_role]

    def __eq__(self, other):
        return type(self) == type(other)

