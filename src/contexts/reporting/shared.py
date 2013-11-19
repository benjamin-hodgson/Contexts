import re
import sys
import traceback
from . import Reporter


class StreamReporter(Reporter):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


class SimpleReporter(Reporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_models = {}
        self.unexpected_errors = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures or self.unexpected_errors
    @property
    def assertions(self):
        return [a for vm in self.view_models.values() for a in vm.assertions.values()]
    @property
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]
    @property
    def context_errors(self):
        return [vm for vm in self.view_models.values() if vm.status == "errored"]

    def context_started(self, context):
        super().context_started(context)
        self.current_context = ContextViewModel(context)
        self.view_models[context] = self.current_context

    def context_ended(self, context):
        super().context_ended(context)
        self.view_models[context].status = "ended"
        self.current_context = None

    def context_errored(self, context, exception):
        self.view_models[context].set_exception(exception)
        self.view_models[context].status = "errored"
        self.current_context = None
        super().context_errored(context, exception)

    def assertion_started(self, assertion):
        super().assertion_started(assertion)
        self.current_context.add_assertion(assertion)

    def assertion_passed(self, assertion):
        assertion_vm = self.current_context.current_assertion
        assertion_vm.status = "passed"
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        assertion_vm = self.current_context.current_assertion
        assertion_vm.status = "failed"
        assertion_vm.set_exception(exception)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        assertion_vm = self.current_context.current_assertion
        assertion_vm.status = "errored"
        assertion_vm.set_exception(exception)
        super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.unexpected_errors.append(format_exception(exception))
        super().unexpected_error(exception)


class ContextViewModel(object):
    def __init__(self, context):
        if hasattr(context.example, "null_example"):
            self.name = make_readable(context.name)
        else:
            self.name = make_readable(context.name) + " -> " + str(context.example)
        self.assertions = {}
        self.error_summary = []
        self.status = "running"

    @property
    def assertion_failures(self):
        return [a for a in self.assertions.values() if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions.values() if a.status == "errored"]

    def add_assertion(self, assertion):
        self.current_assertion = AssertionViewModel(assertion)
        self.current_assertion.status = "running"
        self.assertions[assertion] = self.current_assertion

    def set_exception(self, exception):
        self.error_summary = format_exception(exception)


class AssertionViewModel(object):
    def __init__(self, assertion):
        self.name = make_readable(assertion.name)
        self.status = "running"
        self.error_summary = []

    def set_exception(self, exception):
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
