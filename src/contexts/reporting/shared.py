import re
import sys
import traceback
from . import Reporter


class ReporterComposite(object):
    def __init__(self, reporters):
        self.reporters = reporters

    @property
    def failed(self):
        return any(r.failed for r in self.reporters if hasattr(r, 'failed'))

    def __getattr__(self, name):
        return MethodComposite([getattr(r, name) for r in self.reporters])


class MethodComposite(object):
    def __init__(self, methods):
        self.methods = methods

    def __call__(self, *args, **kwargs):
        for method in self.methods:
            method(*args, **kwargs)


class StreamReporter(Reporter):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


class SimpleReporter(Reporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suite_view_model = SuiteViewModel()

    def context_started(self, context):
        super().context_started(context)
        self.suite_view_model.context_started(context)

    def context_ended(self, context):
        super().context_ended(context)
        self.suite_view_model.context_ended(context)

    def context_errored(self, context, exception):
        self.suite_view_model.context_errored(context, exception)
        super().context_errored(context, exception)

    def assertion_started(self, assertion):
        super().assertion_started(assertion)
        self.suite_view_model.assertion_started(assertion)

    def assertion_passed(self, assertion):
        self.suite_view_model.assertion_passed(assertion)
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        self.suite_view_model.assertion_failed(assertion, exception)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        self.suite_view_model.assertion_errored(assertion, exception)
        super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.suite_view_model.unexpected_error(exception)
        super().unexpected_error(exception)


class SuiteViewModel(object):
    def __init__(self):
        self.unexpected_errors = []
        self.contexts = {}
        self.current_context = None

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures or self.unexpected_errors
    @property
    def assertions(self):
        return [a for vm in self.contexts.values() for a in vm.assertions.values()]
    @property
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]
    @property
    def context_errors(self):
        return [vm for vm in self.contexts.values() if vm.status == "errored"]

    def context_started(self, context):
        self.current_context = ContextViewModel(context)
        self.contexts[context] = self.current_context
    def context_ended(self, context):
        self.contexts[context].status = "ended"
        self.current_context = None
    def context_errored(self, context, exception):
        self.contexts[context].set_exception(exception)
        self.contexts[context].status = "errored"
        self.current_context = None

    def assertion_started(self, assertion):
        self.current_context.add_assertion(assertion)
    def assertion_passed(self, assertion):
        self.current_context.assertions[assertion].status = "passed"
    def assertion_failed(self, assertion, exception):
        assertion_vm = self.current_context.assertions[assertion]
        assertion_vm.status = "failed"
        assertion_vm.set_exception(exception)
    def assertion_errored(self, assertion, exception):
        assertion_vm = self.current_context.assertions[assertion]
        assertion_vm.status = "errored"
        assertion_vm.set_exception(exception)

    def unexpected_error(self, exception):
        self.unexpected_errors.append(format_exception(exception))


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
        view_model = AssertionViewModel(assertion)
        view_model.status = "running"
        self.assertions[assertion] = view_model

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
