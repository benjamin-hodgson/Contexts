import re


establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Ss]et_?[Uu]p)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup|[Tt]ear_?[Dd]own)")


class Spec(object):
    def __init__(self, spec):
        self.spec = spec
        self.result = Result()

    def run_methods_on_class_matching(self, cls, regex):
        for func in find_methods_on_class_matching(cls, regex):
            func(self.spec)

    def run_context(self):
        for cls in reversed(self.spec.__class__.__mro__):
            self.run_methods_on_class_matching(cls, establish_re)

    def run_actions(self):
        self.run_methods_on_class_matching(self.spec.__class__, because_re)

    def run_assertions(self):
        for cls in self.spec.__class__.__mro__:
            for func in find_methods_on_class_matching(cls, should_re):
                try:
                    func(self.spec)
                except AssertionError:
                    self.result.add_failure()
                else:
                    self.result.add_success()

    def run_cleanups(self):
        for cls in self.spec.__class__.__mro__:
            for func in find_methods_on_class_matching(cls, cleanup_re):
                func(self.spec)

    def run(self):
        self.run_context()
        self.run_actions()
        self.run_assertions()
        self.run_cleanups()
        return self.result


def find_methods_on_class_matching(cls, regex):
    ret = []
    for name, func in cls.__dict__.items():
        if re.search(regex, name) and callable(func):
            ret.append(func)
    return ret


class SpecSuite(object):
    def __init__(self, specs):
        self.specs = [Spec(spec) for spec in specs]

    def run(self):
        result = Result()
        for spec in self.specs:
            result += spec.run()
        return result


class Result(object):
    def __init__(self, assertions=0, failures=0):
        self.assertions = assertions
        self.failures = failures

    def add_success(self):
        self.assertions += 1

    def add_failure(self):
        self.assertions += 1
        self.failures += 1

    def summary(self):
        return "{} assertions, {} failed".format(self.assertions, self.failures)

    def __add__(self, other):
        assertions = self.assertions + other.assertions
        failures = self.failures + other.failures
        return Result(assertions, failures)
