import re
from . import EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN

example_re = re.compile(r"[Ee]xample|[Dd]ata")
establish_re = re.compile(r"[Ee]stablish|[Cc]ontext|[Gg]iven")
because_re = re.compile(r"[Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter")
should_re = re.compile(r"[Ss]hould|((^|[a-z]|_)I|(^|_)i)t|[Mm]ust|[Ww]ill|[Tt]hen")
cleanup_re = re.compile(r"[Cc]leanup")


class NameBasedIdentifier(object):
    def identify_method(self, method):
        if example_re.search(method.__name__):
            return EXAMPLES
        elif establish_re.search(method.__name__):
            return SETUP
        elif because_re.search(method.__name__):
            return ACTION
        elif should_re.search(method.__name__):
            return ASSERTION
        elif cleanup_re.search(method.__name__):
            return TEARDOWN
