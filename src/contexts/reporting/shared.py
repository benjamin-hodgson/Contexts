import re
import traceback
from contextlib import contextmanager
from . import Reporter


class ReporterNotifier(object):
    def __init__(self, *reporters):
        self.reporters = []
        for reporter in reporters:
            self.reporters.append(reporter)

    @property
    def failed(self):
        return any(r.failed for r in self.reporters if hasattr(r, 'failed'))

    def call_reporters(self, method, *args):
        for reporter in self.reporters:
            getattr(reporter, method)(*args)

    @contextmanager
    def run_suite(self, suite):
        self.call_reporters("suite_started", suite)
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)
        self.call_reporters("suite_ended", suite)

    @contextmanager
    def run_context(self, context):
        self.call_reporters("context_started", context)
        try:
            yield
        except Exception as e:
            self.call_reporters("context_errored", context, e)
        else:
            self.call_reporters("context_ended", context)

    @contextmanager
    def run_assertion(self, assertion):
        self.call_reporters("assertion_started", assertion)
        try:
            yield
        except AssertionError as e:
            self.call_reporters("assertion_failed", assertion, e)
        except Exception as e:
            self.call_reporters("assertion_errored", assertion, e)
        else:
            self.call_reporters("assertion_passed", assertion)

    @contextmanager
    def run_class(self, cls):
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)

    @contextmanager
    def importing(self, module_spec):
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)


class StreamReporter(Reporter):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


def make_readable(string):
    regex = re.compile(r'(_|\.|{}|{}|{})'.format(
        r'(?<=[^A-Z])(?=[A-Z])',
        r'(?<=[A-Z])(?=[A-Z][a-z])',
        r'(?<=[A-Za-z])(?=[^A-Za-z])'
    ))
    words = regex.sub(' ', string).split(' ')

    cased_words = [words[0]]
    for word in words[1:]:
        should_lowerise = (not word.isupper()) or (len(word) == 1)
        cased_word = word.lower() if should_lowerise else word
        cased_words.append(cased_word)
    return ' '.join(cased_words)


def context_name(context):
    if hasattr(context.example, "null_example"):
        return make_readable(context.name)
    else:
        return make_readable(context.name) + " -> " + str(context.example)


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    # exception.__traceback__ = None
    return ''.join(ret).strip().split('\n')
