import re
import traceback
from contextlib import contextmanager
from . import Reporter


class ReporterNotifier(object):
    def __init__(self, manager):
        self.manager = manager

    @classmethod
    def from_reporters(cls, *reporters):
        manager = ReporterManager(*reporters)
        return cls(manager)

    @property
    def failed(self):
        return self.manager.failed
    @property
    def suite_view_model(self):
        return self.manager.suite_view_model
    @suite_view_model.setter
    def suite_view_model(self, value):
        self.manager.suite_view_model = value

    def suite_started(self, suite):
        self.manager.suite_started(suite)
    def suite_ended(self, suite):
        self.manager.suite_ended(suite)

    def context_started(self, context):
        self.manager.context_started(context)
    def context_ended(self, context):
        self.manager.context_ended(context)
    def context_errored(self, context, exception):
        self.manager.context_errored(context, exception)

    def assertion_started(self, assertion):
        self.manager.assertion_started(assertion)
    def assertion_passed(self, assertion):
        self.manager.assertion_passed(assertion)
    def assertion_failed(self, assertion, exception):
        self.manager.assertion_failed(assertion, exception)
    def assertion_errored(self, assertion, exception):
        self.manager.assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.manager.unexpected_error(exception)

    @contextmanager
    def run_suite(self, suite):
        self.manager.suite_started(suite)
        try:
            yield
        except Exception as e:
            self.manager.unexpected_error(e)
        self.manager.suite_ended(suite)

    @contextmanager
    def run_context(self, context):
        self.manager.context_started(context)
        try:
            yield
        except Exception as e:
            self.manager.context_errored(context, e)
        else:
            self.manager.context_ended(context)

    @contextmanager
    def run_assertion(self, assertion):
        self.manager.assertion_started(assertion)
        try:
            yield
        except AssertionError as e:
            self.manager.assertion_failed(assertion, e)
        except Exception as e:
            self.manager.assertion_errored(assertion, e)
        else:
            self.manager.assertion_passed(assertion)

    @contextmanager
    def run_class(self, cls):
        try:
            yield
        except Exception as e:
            self.manager.unexpected_error(e)

    @contextmanager
    def importing(self, module_spec):
        try:
            yield
        except Exception as e:
            self.manager.unexpected_error(e)


class ReporterManager(Reporter):
    def __init__(self, *reporters):
        self.reporters = []
        self.suite_view_model = SuiteViewModel()
        for reporter in reporters:
            self.reporters.append(reporter)
            reporter.suite_view_model = self.suite_view_model  # is this a good idea?

    @property
    def failed(self):
        return self.suite_view_model.failed

    # TODO: abstract this
    def suite_started(self, suite):
        self.call_reporters("suite_started", suite)
    def suite_ended(self, suite):
        self.call_reporters("suite_ended", suite)

    def context_started(self, context):
        self.suite_view_model.context_started(context)
        self.call_reporters("context_started", context)
    def context_ended(self, context):
        self.suite_view_model.context_ended(context)
        self.call_reporters("context_ended", context)
    def context_errored(self, context, exception):
        self.suite_view_model.context_errored(context, exception)
        self.call_reporters("context_errored", context, exception)

    def assertion_started(self, assertion):
        self.suite_view_model.assertion_started(assertion)
        self.call_reporters("assertion_started", assertion)
    def assertion_passed(self, assertion):
        self.suite_view_model.assertion_passed(assertion)
        self.call_reporters("assertion_passed", assertion)
    def assertion_failed(self, assertion, exception):
        self.suite_view_model.assertion_failed(assertion, exception)
        self.call_reporters("assertion_failed", assertion, exception)
    def assertion_errored(self, assertion, exception):
        self.suite_view_model.assertion_errored(assertion, exception)
        self.call_reporters("assertion_errored", assertion, exception)

    def unexpected_error(self, exception):
        self.suite_view_model.unexpected_error(exception)
        self.call_reporters("unexpected_error", exception)

    def call_reporters(self, method, *args):
        for reporter in self.reporters:
            getattr(reporter, method)(*args)


class StreamReporter(Reporter):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


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

    def suite_started(self, suite):
        pass
    def suite_ended(self, suite):
        pass

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
    def failed(self):
        return self.assertion_failures or self.assertion_errors or self.error_summary

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
