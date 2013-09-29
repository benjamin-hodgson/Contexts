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
        self.establish = no_op
        self.because = no_op
        self.shoulds = []
        self.cleanup = no_op
        for name, meth in inspect.getmembers(spec, inspect.ismethod):
            if re.search(establish_re, name):
                self.establish = meth
            if re.search(because_re, name):
                self.because = meth
            if re.search(should_re, name):
                self.shoulds.append(meth)
            if re.search(cleanup_re, name):
                self.cleanup = meth

    def run(self):
        self.establish()
        self.because()
        for should in self.shoulds:
            should()
        self.cleanup()


def run(spec):
    Spec(spec).run()
