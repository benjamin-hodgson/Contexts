import re
import types


establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Ss]et_?[Uu]p)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup|[Tt]ear_?[Dd]own)")


def find_methods_matching(spec, regex, *, top_down=False, one_only=False):
    ret = []
    mro = spec.__class__.__mro__
    classes = reversed(mro) if top_down else mro
    for cls in classes:
        for name, func in cls.__dict__.items():
            if re.search(regex, name) and callable(func):
                method = types.MethodType(func, spec)
                ret.append(method)
                if one_only:
                    return ret
    return ret


class Assertion(object):
    def __init__(self, func):
        self.func = func
        self.result = None
        self.exception = None

    def __call__(self):
        try:
            self.func()
        except AssertionError as e:
            self.exception = e
            self.result = "failed"
        except Exception as e:
            self.exception = e
            self.result = "errored"
        else:
            self.result = "succeeded"


class Context(object):
    def __init__(self, spec):
        self.spec = spec
        self.exception = None
        self.setups = find_methods_matching(spec, establish_re, top_down=True)
        self.actions = find_methods_matching(spec, because_re, one_only=True)
        self.assertions = [Assertion(f) for f in find_methods_matching(spec, should_re)]
        self.teardowns = find_methods_matching(spec, cleanup_re)

    def run_setup(self):
        for setup in self.setups:
            setup()

    def run_action(self):
        for action in self.actions:
            action()

    def run_assertions(self):
        for assertion in self.assertions:
            assertion()

    def run_teardown(self):
        for teardown in self.teardowns:
            teardown()

    @property
    def result(self):
        return Result([self])

    def run(self):
        try:
            self.run_setup()
            self.run_action()
            self.run_assertions()
            self.run_teardown()
        except Exception:
            for assertion in self.assertions:
                assertion.result = "errored"
        return self.result


class Result(object):
    def __init__(self, contexts=None):
        self.contexts = contexts if contexts is not None else []

    @property
    def assertions(self):
        return [a for c in self.contexts for a in c.assertions]

    @property
    def failures(self):
        return [a for a in self.assertions if a.result == "failed"]

    @property
    def errors(self):
        return [a for a in self.assertions if a.result == "errored"]

    def summary(self):
        ret = "{} contexts, {} assertions".format(len(self.contexts), len(self.assertions))
        if self.failures or self.errors:
            ret += ", {} failed, {} errors".format(len(self.failures), len(self.errors))
        return ret

    def __add__(self, other):
        contexts = self.contexts + other.contexts
        return Result(contexts)
