import inspect
import re

establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill)")
cleanup_re = re.compile(r"(^|_)([Cc]leanup)")


def no_op():
    pass


class Spec(object):
    def __init__(self, spec):
        self.spec = spec

    def find_methods_matching(self, regex):
        for name, meth in inspect.getmembers(self.spec, inspect.ismethod):
            if re.search(regex, name):
                yield meth

    def run_methods_matching(self, regex):
        for method in self.find_methods_matching(regex):
            method()

    def run(self):
        self.run_methods_matching(establish_re)
        self.run_methods_matching(because_re)
        self.run_methods_matching(should_re)
        self.run_methods_matching(cleanup_re)


def run(spec):
    Spec(spec).run()
