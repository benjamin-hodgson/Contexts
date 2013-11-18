import re
import sys
import traceback
from . import Reporter


class SimpleReporter(Reporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_models = []
        self.unexpected_errors = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures or self.unexpected_errors
    @property
    def assertions(self):
        return [a for vm in self.view_models for a in vm.assertions]
    @property
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]
    @property
    def contexts(self):
        return self.view_models
    @property
    def context_errors(self):
        return [vm for vm in self.view_models if vm.error_summary is not None]
    @property
    def current_context(self):
        return self.view_models[-1]

    def context_started(self, context):
        super().context_started(context)
        self.view_models.append(ContextViewModel(context))

    def context_errored(self, context, exception):
        self.current_context.exception = exception
        super().context_errored(context, exception)

    def assertion_passed(self, assertion):
        assertion_vm = AssertionViewModel(assertion)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        assertion_vm = AssertionViewModel(assertion, "failed", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        assertion_vm = AssertionViewModel(assertion, "errored", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.unexpected_errors.append(format_exception(exception))
        super().unexpected_error(exception)


class StreamReporter(Reporter):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


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
