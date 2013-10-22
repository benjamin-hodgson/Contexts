import datetime
import sys
import traceback
from .core import Result


class SimpleResult(Result):
    def __init__(self):
        self.contexts = []
        self.assertions = []
        self.context_errors = []
        self.assertion_errors = []
        self.assertion_failures = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures
    
    def context_ran(self, context):
        self.contexts.append(context)
        super().context_ran(context)

    def context_errored(self, context, exception, extracted_traceback):
        self.contexts.append(context)
        self.context_errors.append((context, exception, extracted_traceback))
        super().context_errored(context, exception, extracted_traceback)

    def assertion_passed(self, assertion):
        self.assertions.append(assertion)
        super().assertion_passed(assertion)

    def assertion_errored(self, assertion, exception, extracted_traceback):
        self.assertions.append(assertion)
        self.assertion_errors.append((assertion, exception, extracted_traceback))
        super().assertion_errored(assertion, exception, extracted_traceback)

    def assertion_failed(self, assertion, exception, extracted_traceback):
        self.assertions.append(assertion)
        self.assertion_failures.append((assertion, exception, extracted_traceback))
        super().assertion_failed(assertion, exception, extracted_traceback)


class TextResult(SimpleResult):
    dashes = '-' * 70
    equalses = '=' * 70

    def __init__(self, stream=sys.stderr):
        self.stream = stream
        super().__init__()

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)

    def suite_ended(self, suite):
        self.summarise()
        super().suite_ended(suite)

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

    def summarise(self):
        self._print('')
        if self.failed:
            for tup in self.context_errors + self.assertion_errors + self.assertion_failures:
                self.print_assertion_failure(*tup)
        self._print(self.dashes)
        if self.failed:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def print_assertion_failure(self, assertion, exception, extracted_tb):
        self._print(self.equalses)
        self._print("FAIL:" if isinstance(exception, AssertionError) else "ERROR:", assertion.name)
        self._print(self.dashes)
        self._print("Traceback (most recent call last):")
        self._print(''.join(traceback.format_list(extracted_tb)), end='')
        self._print(''.join(traceback.format_exception_only(exception.__class__, exception)), end='')

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

    def summarise(self):
        super().summarise()
        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))
