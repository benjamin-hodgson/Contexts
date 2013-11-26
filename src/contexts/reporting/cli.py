import datetime
import sys
from contextlib import contextmanager
from io import StringIO
import colorama
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


class VerboseReporter(shared.StreamReporter):
    dashes = '-' * 70
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_indent = ''

    def indent(self):
        self.current_indent += '  '

    def dedent(self):
        self.current_indent = self.current_indent[:-2]

    def _print(self, string, *args, **kwargs):
        lines = string.split('\n')
        for i, line in enumerate(lines[:]):
            lines[i] = self.current_indent + line
        super()._print('\n'.join(lines), *args, **kwargs)

    def context_started(self, context):
        super().context_started(context)
        self._print(self.suite_view_model.contexts[context].name)
        self.indent()

    def context_ended(self, context):
        self.dedent()
        super().context_ended(context)

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        self._print('\n'.join(self.suite_view_model.contexts[context].error_summary))
        self.dedent()

    def assertion_passed(self, assertion):
        super().assertion_started(assertion)
        self._print('PASS: ' + self.suite_view_model.current_context.assertions[assertion].name)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        vm = self.suite_view_model.current_context.assertions[assertion]
        self._print('FAIL: ' + vm.name)
        self.indent()
        self._print('\n'.join(vm.error_summary))
        self.dedent()

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        vm = self.suite_view_model.current_context.assertions[assertion]
        self._print('ERROR: ' + vm.name)
        self.indent()
        self._print('\n'.join(vm.error_summary))
        self.dedent()

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        self._print('\n'.join(self.suite_view_model.unexpected_errors[-1]))

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

    def summarise(self):
        self._print('')
        self._print(self.dashes)
        if self.suite_view_model.failed:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def success_numbers(self):
        return "{}, {}".format(
            pluralise("context", len(self.suite_view_model.contexts)),
            pluralise("assertion", len(self.suite_view_model.assertions)))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", len(self.suite_view_model.contexts)),
            pluralise("assertion", len(self.suite_view_model.assertions)),
            len(self.suite_view_model.assertion_failures),
            pluralise("error", len(self.suite_view_model.assertion_errors) + len(self.suite_view_model.context_errors) + len(self.suite_view_model.unexpected_errors)))


class ColouredReporter(VerboseReporter):
    def context_errored(self, context, exception):
        with self.red():
            super().context_errored(context, exception)

    def assertion_passed(self, assertion):
        with self.green():
            super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        with self.red():
            super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        with self.red():
            super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        with self.red():
            super().unexpected_error(exception)

    @contextmanager
    def red(self):
        self.stream.write(colorama.Fore.RED)
        yield
        self.stream.write(colorama.Fore.RESET)

    @contextmanager
    def green(self):
        self.stream.write(colorama.Fore.GREEN)
        yield
        self.stream.write(colorama.Fore.RESET)


class SummarisingReporter(VerboseReporter):
    def __init__(self, stream):
        super().__init__(stream)
        self.real_stream = stream
        self.stream = StringIO()
        self.to_output_at_end = StringIO()

    def context_started(self, context):
        self.current_context_failed = False
        super().context_started(context)

    def context_ended(self, context):
        super().context_ended(context)
        if self.current_context_failed:
            self.to_output_at_end.write(self.stream.getvalue())
        self.stream = StringIO()

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        self.to_output_at_end.write(self.stream.getvalue())
        self.stream = StringIO()

    def assertion_passed(self, assertion):
        orig_stream = self.stream
        self.stream = StringIO()
        super().assertion_passed(assertion)
        self.stream = orig_stream

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.current_context_failed = True

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.current_context_failed = True

    def unexpected_error(self, exception):
        orig_stream = self.stream
        self.stream = self.to_output_at_end
        super().unexpected_error(exception)
        self.stream = orig_stream

    def suite_ended(self, suite):
        output = self.to_output_at_end.getvalue()
        if output:
            self.real_stream.write('\n' + self.dashes + '\n')
            self.real_stream.write(output.strip())

        self.stream = self.real_stream
        super().suite_ended(suite)


class StdOutCapturingReporter(SummarisingReporter):
    def centred_dashes(self, string):
        num = str(70 - len(self.current_indent))
        return ("{:-^"+num+"}").format(string)

    def context_started(self, context):
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer
        super().context_started(context)

    def context_ended(self, context):
        sys.stdout = self.real_stdout
        super().context_ended(context)

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        sys.stdout = self.real_stdout
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
            self._print(self.centred_dashes(" >> begin captured stdout << "))
            self._print(self.buffer.getvalue().strip())
            self._print(self.centred_dashes(" >> end captured stdout << "))
            self.dedent()


class TimedReporter(shared.StreamReporter):
    def suite_started(self, suite):
        super().suite_started(suite)
        self.start_time = datetime.datetime.now()

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.end_time = datetime.datetime.now()
        self.print_time()

    def print_time(self):
        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
