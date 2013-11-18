import sys
from . import Reporter, view_models


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
        self.view_models.append(view_models.ContextViewModel(context))

    def context_errored(self, context, exception):
        self.current_context.exception = exception
        super().context_errored(context, exception)

    def assertion_passed(self, assertion):
        assertion_vm = view_models.AssertionViewModel(assertion)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        assertion_vm = view_models.AssertionViewModel(assertion, "failed", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        assertion_vm = view_models.AssertionViewModel(assertion, "errored", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.unexpected_errors.append(view_models.format_exception(exception))
        super().unexpected_error(exception)


class StreamReporter(Reporter):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
