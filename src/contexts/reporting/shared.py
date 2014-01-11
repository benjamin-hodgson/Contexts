import re
import traceback
from . import Reporter


class StreamReporter(Reporter):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)

    def __eq__(self, other):
        return type(self) == type(other) and self.stream == other.stream


class CountingReporter(Reporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_count = 0
        self.assertion_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.failed = False

    def context_started(self, name, example):
        super().context_started(name, example)
        self.context_count += 1

    def context_errored(self, name, example, exception):
        super().context_errored(name, example, exception)
        self.error_count += 1
        self.failed = True

    def assertion_started(self, assertion):
        super().assertion_started(assertion)
        self.assertion_count += 1

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.failure_count += 1
        self.failed = True

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.error_count += 1
        self.failed = True

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        self.error_count += 1
        self.failed = True


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


def context_name(name, example):
    if hasattr(example, "null_example"):
        return make_readable(name)
    else:
        return make_readable(name) + " -> " + str(example)


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    # exception.__traceback__ = None
    return ''.join(ret).strip().split('\n')
