import datetime
import sys
from io import StringIO
from . import shared


class DotsReporter(shared.StreamReporter):
    def assertion_passed(self, *args, **kwargs):
        super().assertion_passed(*args, **kwargs)
        self._print('.', end='')

    def assertion_failed(self, *args, **kwargs):
        super().assertion_failed(*args, **kwargs)
        self._print('F', end='')

    def assertion_errored(self, *args, **kwargs):
        super().assertion_errored(*args, **kwargs)
        self._print('E', end='')

    def context_errored(self, *args, **kwargs):
        super().context_errored(*args, **kwargs)
        self._print('E', end='')

    def unexpected_error(self, *args, **kwargs):
        super().unexpected_error(*args, **kwargs)
        self._print('E', end='')


class SummarisingReporter(shared.SimpleReporter, shared.StreamReporter):
    dashes = '-' * 70

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary = []
        self.current_summary = None
        self.current_indent = ''

    def context_started(self, context):
        super().context_started(context)
        self.current_summary = [self.view_models[context].name]
        self.indent()

    def context_ended(self, context):
        super().context_ended(context)
        ctx = self.view_models[context]
        if ctx.assertion_failures or ctx.assertion_errors:
            self.add_current_context_to_summary()
        self.dedent()
        self.current_summary = None

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        ctx = self.view_models[context]
        formatted_exc = ctx.error_summary
        self.extend_summary(formatted_exc)
        self.add_current_context_to_summary()
        self.dedent()
        self.current_summary = None

    def assertion_started(self, assertion):
        super().assertion_started(assertion)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.add_current_assertion_to_summary()

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.add_current_assertion_to_summary()

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        formatted_exc = self.unexpected_errors[-1]
        self.extend_summary(formatted_exc)

    def indent(self):
        self.current_indent += '  '

    def dedent(self):
        self.current_indent = self.current_indent[:-2]

    def append_to_summary(self, string):
        if self.current_summary is not None:
            self.current_summary.append(self.current_indent + string)
        else:
            self.summary.append(self.current_indent + string)

    def extend_summary(self, iterable):
        if self.current_summary is not None:
            self.current_summary.extend(self.current_indent + s for s in iterable)
        else:
            self.summary.extend(self.current_indent + s for s in iterable)

    def add_current_context_to_summary(self):
        self.summary.extend(self.current_summary)

    def add_current_assertion_to_summary(self):
        assertion_vm = self.current_context.current_assertion
        formatted_exc = assertion_vm.error_summary

        if assertion_vm.status == "errored":
            self.append_to_summary('ERROR: ' + assertion_vm.name)
        elif assertion_vm.status == "failed":
            self.append_to_summary('FAIL: ' + assertion_vm.name)

        self.indent()
        self.extend_summary(formatted_exc)
        self.dedent()

    def summarise(self):
        self._print('')
        self._print(self.dashes)
        if self.failed:
            self._print('\n'.join(self.summary))
            self._print(self.dashes)
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def success_numbers(self):
        return "{}, {}".format(
            pluralise("context", len(self.view_models)),
            pluralise("assertion", len(self.assertions)))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", len(self.view_models)),
            pluralise("assertion", len(self.assertions)),
            len(self.assertion_failures),
            pluralise("error", len(self.assertion_errors) + len(self.context_errors) + len(self.unexpected_errors)))


class VerboseReporter(shared.SimpleReporter, shared.StreamReporter):
    dashes = '-' * 70
    
    def context_started(self, context):
        super().context_started(context)
        self._print(self.view_models[context].name)

    def assertion_passed(self, assertion):
        super().assertion_started(assertion)
        self._print('  PASS: ' + self.current_context.assertions[assertion].name)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        vm = self.current_context.assertions[assertion]
        self._print('  FAIL: ' + vm.name)
        self._print('    ' + '\n    '.join(vm.error_summary))

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        vm = self.current_context.assertions[assertion]
        self._print('  ERROR: ' + vm.name)
        self._print('    ' + '\n    '.join(vm.error_summary))

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        self._print('  ' + '\n  '.join(self.view_models[context].error_summary))

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

    def summarise(self):
        self._print(self.dashes)
        if self.failed:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def success_numbers(self):
        return "{}, {}".format(
            pluralise("context", len(self.view_models)),
            pluralise("assertion", len(self.assertions)))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", len(self.view_models)),
            pluralise("assertion", len(self.assertions)),
            len(self.assertion_failures),
            pluralise("error", len(self.assertion_errors) + len(self.context_errors) + len(self.unexpected_errors)))


class StdOutCapturingReporter(SummarisingReporter):
    def context_started(self, context):
        super().context_started(context)
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer

    def centred_dashes(self, string):
        num = str(70 - len(self.current_indent))
        return ("{:-^"+num+"}").format(string)

    def context_ended(self, context):
        sys.stdout = self.real_stdout
        super().context_ended(context)

    def context_errored(self, context, exception):
        sys.stdout = self.real_stdout
        super().context_errored(context, exception)
        self.add_buffer_to_summary()

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.add_buffer_to_summary()

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.add_buffer_to_summary()

    def add_buffer_to_summary(self):
        if self.buffer.getvalue():
            self.indent()
            self.append_to_summary(self.centred_dashes(" >> begin captured stdout << "))
            self.extend_summary(self.buffer.getvalue().strip().split('\n'))
            self.append_to_summary(self.centred_dashes(" >> end captured stdout << "))
            self.dedent()


class TimedReporter(shared.StreamReporter):
    def suite_started(self, suite):
        super().suite_started(suite)
        self.start_time = datetime.datetime.now()

    def suite_ended(self, suite):
        self.end_time = datetime.datetime.now()
        super().suite_ended(suite)

        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
