import inspect
import re

establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Ss]et_?[Uu]p)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup|[Tt]ear_?[Dd]own)")


def no_op():
    pass


class Spec(object):
    def __init__(self, spec):
        self.spec = spec
        self.result = Result()

    def find_methods_matching(self, regex):
        for name, meth in inspect.getmembers(self.spec, inspect.ismethod):
            if re.search(regex, name):
                yield meth

    def run_methods_matching(self, regex):
        for method in self.find_methods_matching(regex):
            method()

    def run_assertions(self):
        for method in self.find_methods_matching(should_re):
            try:
                method()
            except AssertionError:
                self.result.add_failure()
            else:
                self.result.add_success()

    def run(self):
        self.run_methods_matching(establish_re)
        self.run_methods_matching(because_re)
        self.run_assertions()
        self.run_methods_matching(cleanup_re)
        return self.result


class Result(object):
    def __init__(self):
        self.assertions = 0
        self.failures = 0

    def add_success(self):
        self.assertions += 1

    def add_failure(self):
        self.assertions += 1
        self.failures += 1

    def summary(self):
        return "{} assertions, {} failed".format(self.assertions, self.failures)


def run(spec):
    return Spec(spec).run()
