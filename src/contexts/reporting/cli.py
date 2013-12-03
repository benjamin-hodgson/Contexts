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
        self.context_count = 0
        self.assertion_count = 0
        self.failure_count = 0
        self.error_count = 0

    def context_started(self, context):
        super().context_started(context)
        self.context_count += 1
        self._print(shared.context_name(context))

    def context_errored(self, context, exception):
        self.error_count += 1
        super().context_errored(context, exception)
        for line in shared.format_exception(exception):
            self._print('  ' + line)

    def assertion_started(self, assertion):
        self.assertion_count += 1
        super().assertion_started(assertion)

    def assertion_passed(self, assertion):
        super().assertion_started(assertion)
        self._print('  PASS: ' + shared.make_readable(assertion.name))

    def assertion_failed(self, assertion, exception):
        self.failure_count += 1

        super().assertion_failed(assertion, exception)

        self._print('  FAIL: ' + shared.make_readable(assertion.name))
        for line in shared.format_exception(exception):
            self._print('    ' + line)

    def assertion_errored(self, assertion, exception):
        self.error_count += 1

        super().assertion_errored(assertion, exception)

        self._print('  ERROR: ' + shared.make_readable(assertion.name))
        for line in shared.format_exception(exception):
            self._print('    ' + line)

    def unexpected_error(self, exception):
        self.error_count += 1
        super().unexpected_error(exception)
        for line in shared.format_exception(exception):
            self._print(line)

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

    def summarise(self):
        self._print('')
        self._print(self.dashes)
        if self.failure_count or self.error_count:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def success_numbers(self):
        return "{}, {}".format(
            pluralise("context", self.context_count),
            pluralise("assertion", self.assertion_count))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", self.context_count),
            pluralise("assertion", self.assertion_count),
            self.failure_count,
            pluralise("error", self.error_count))


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


class StdOutCapturingReporter(VerboseReporter):
    def centred_dashes(self, string, indentation):
        num = str(70 - indentation)
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
        self.add_buffer_to_summary(2)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.add_buffer_to_summary(4)

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.add_buffer_to_summary(4)

    def add_buffer_to_summary(self, indentation):
        if self.buffer.getvalue():
            lines = [self.centred_dashes(" >> begin captured stdout << ", indentation)]
            lines.extend(self.buffer.getvalue().strip().split('\n'))
            lines.append(self.centred_dashes(" >> end captured stdout << ", indentation))
            for line in lines:
                self._print(' '*(indentation) + line)


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
