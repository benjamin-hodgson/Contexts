import abc
import datetime
import sys
import traceback
from io import StringIO


class Result(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def failed(self):
        return True

    def suite_started(self, suite):
        """Called at the beginning of a test run"""

    def suite_ended(self, suite):
        """Called at the end of a test run"""

    def context_started(self, context):
        """Called when a test context begins its run"""

    def context_ended(self, context):
        """Called when a test context completes its run"""

    def context_errored(self, context, exception, extracted_traceback):
        """Called when a test context (not an assertion) throws an exception"""

    def assertion_started(self, assertion):
        """Called when an assertion begins"""

    def assertion_passed(self, assertion):
        """Called when an assertion passes"""

    def assertion_errored(self, assertion, exception, extracted_traceback):
        """Called when an assertion throws an exception"""

    def assertion_failed(self, assertion, exception, extracted_traceback):
        """Called when an assertion throws an AssertionError"""


class SimpleResult(Result):
    def __init__(self):
        self.contexts = []
        self.assertions = []
        self.context_errors = []
        self.assertion_errors = []
        self.assertion_failures = []
        super().__init__()

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures

    def context_started(self, context):
        self.contexts.append(context)
        super().context_started(context)

    def context_errored(self, context, exception, extracted_tb):
        self.context_errors.append((context, exception, extracted_tb))
        super().context_errored(context, exception, extracted_tb)

    def assertion_started(self, assertion):
        self.assertions.append(assertion)
        super().assertion_started(assertion)

    def assertion_errored(self, assertion, exception, extracted_tb):
        self.assertion_errors.append((assertion, exception, extracted_tb))
        super().assertion_errored(assertion, exception, extracted_tb)

    def assertion_failed(self, assertion, exception, extracted_tb):
        self.assertion_failures.append((assertion, exception, extracted_tb))
        super().assertion_failed(assertion, exception, extracted_tb)


class TextResult(SimpleResult):
    dashes = '-' * 70
    equalses = '=' * 70

    def __init__(self, stream=sys.stderr):
        self.stream = stream
        self.summary = []
        super().__init__()

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)

    def suite_ended(self, suite):
        self.summarise()
        super().suite_ended(suite)

    def assertion_passed(self, *args, **kwargs):
        super().assertion_passed(*args, **kwargs)
        self._print('.', end='')

    def assertion_failed(self, assertion, exception, extracted_tb):
        super().assertion_failed(assertion, exception, extracted_tb)
        self._print('F', end='')
        self.summary.extend(self.format_failure(assertion, exception, extracted_tb, "FAIL"))

    def assertion_errored(self, assertion, exception, extracted_tb):
        super().assertion_errored(assertion, exception, extracted_tb)
        self._print('E', end='')
        self.summary.extend(self.format_failure(assertion, exception, extracted_tb, "ERROR"))

    def context_errored(self, context, exception, extracted_tb):
        super().context_errored(context, exception, extracted_tb)
        self._print('E', end='')
        self.summary.extend(self.format_failure(context, exception, extracted_tb, "ERROR"))

    def summarise(self):
        self._print('')
        if self.failed:
            self._print('\n'.join(self.summary))
        self._print(self.dashes)
        if self.failed:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def format_failure(self, assertion, exception, extracted_tb, word):
        formatted = [
            self.equalses,
            "{}: {}".format(word, assertion.name),
            self.dashes,
            "Traceback (most recent call last):"
        ]
        formatted.extend(s[:-1] for s in traceback.format_list(extracted_tb))
        formatted.extend(s[:-1] for s in traceback.format_exception_only(exception.__class__, exception))
        return formatted

    def success_numbers(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        msg = "{}, {}".format(pluralise("context", num_ctx), pluralise("assertion", num_ass))
        return msg

    def failure_numbers(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        num_ctx_err = len(self.context_errors)
        num_fail = len(self.assertion_failures)
        num_err = len(self.assertion_errors)
        msg =  "{}, {}: {} failed, {}".format(pluralise("context", num_ctx),
           pluralise("assertion", num_ass),
           num_fail,
           pluralise("error", num_err + num_ctx_err))
        return msg


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string


class TimedTextResult(TextResult):
    def suite_started(self, suite):
        self.start_time = datetime.datetime.now()

    def suite_ended(self, suite):
        self.end_time = datetime.datetime.now()
        super().suite_ended(suite)

    def summarise(self):
        super().summarise()
        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


class CapturingTextResult(TextResult):
    def context_started(self, context):
        super().context_started(context)
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer

    def context_ended(self, context):
        sys.stdout = self.real_stdout
        super().context_ended(context)

    def context_errored(self, context, exception, extracted_tb):
        sys.stdout = self.real_stdout
        super().context_errored(context, exception, extracted_tb)
        self.append_buffer_to_summary()

    def assertion_failed(self, assertion, exception, extracted_tb):
        super().assertion_failed(assertion, exception, extracted_tb)
        self.append_buffer_to_summary()

    def assertion_errored(self, assertion, exception, extracted_tb):
        super().assertion_errored(assertion, exception, extracted_tb)
        self.append_buffer_to_summary()

    def append_buffer_to_summary(self):
        if self.buffer.getvalue():
            self.summary.append("-------------------- >> begin captured stdout << ---------------------")
            self.summary.append(self.buffer.getvalue()[:-1])
            self.summary.append("--------------------- >> end captured stdout << ----------------------")


class TimedCapturingTextResult(TimedTextResult, CapturingTextResult):
    pass

