import re
import traceback


class ContextViewModel(object):
    def __init__(self, context):
        if hasattr(context.example, "null_example"):
            self.name = make_readable(context.name)
        else:
            self.name = make_readable(context.name) + " -> " + str(context.example)
        self.assertions = []
        self._exception = None
        self.error_summary = None

    @property
    def exception(self):
        return self._exception
    @exception.setter
    def exception(self, value):
        self._exception = value
        self.error_summary = format_exception(value)

    @property
    def last_assertion(self):
        return self.assertions[-1]

    @property
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]


class AssertionViewModel(object):
    def __init__(self, assertion, status="passed", exception=None):
        self.name = make_readable(assertion.name)
        self.status = status
        self.error_summary = None
        if exception is not None:
            self.error_summary = format_exception(exception)


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


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    exception.__traceback__ = None
    return ''.join(ret).strip().split('\n')
