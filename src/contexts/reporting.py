import abc
import datetime
import sys
import traceback
from io import StringIO


class Result(object):
    @property
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

    def context_errored(self, context, exception):
        """Called when a test context (not an assertion) throws an exception"""

    def assertion_started(self, assertion):
        """Called when an assertion begins"""

    def assertion_passed(self, assertion):
        """Called when an assertion passes"""

    def assertion_errored(self, assertion, exception):
        """Called when an assertion throws an exception"""

    def assertion_failed(self, assertion, exception):
        """Called when an assertion throws an AssertionError"""


class ContextViewModel(object):
    def __init__(self, context):
        self.name = context.name
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
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]


class AssertionViewModel(object):
    def __init__(self, assertion, status="passed", exception=None):
        self.name = assertion.name
        self.status = status
        self.error_summary = None
        if exception is not None:
            self.error_summary = format_exception(exception)


class SimpleResult(Result):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_models = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures
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

    def context_started(self, context):
        super().context_started(context)
        self.view_models.append(ContextViewModel(context))

    def context_errored(self, context, exception):
        context_vm = self.view_models[-1]
        context_vm.exception = exception
        super().context_errored(context, exception)

    def assertion_passed(self, assertion):
        context_vm = self.view_models[-1]
        assertion_vm = AssertionViewModel(assertion)
        context_vm.assertions.append(assertion_vm)
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        context_vm = self.view_models[-1]
        assertion_vm = AssertionViewModel(assertion, "failed", exception)
        context_vm.assertions.append(assertion_vm)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        context_vm = self.view_models[-1]
        assertion_vm = AssertionViewModel(assertion, "errored", exception)
        context_vm.assertions.append(assertion_vm)
        super().assertion_errored(assertion, exception)


class StreamResult(Result):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


class DotsResult(StreamResult):
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


class SummarisingResult(SimpleResult, StreamResult):
    dashes = '-' * 70
    equalses = '=' * 70

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary = []

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

    def assertion_failed(self, assertion, exception):
        self.summary.extend(self.format_failure(assertion, exception, "FAIL"))
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        self.summary.extend(self.format_failure(assertion, exception, "ERROR"))
        super().assertion_errored(assertion, exception)

    def context_errored(self, context, exception):
        self.summary.extend(self.format_failure(context, exception, "ERROR"))
        super().context_errored(context, exception)

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

    def format_failure(self, assertion, exception, word):
        formatted = [
            self.equalses,
            "{}: {}".format(word, assertion.name),
            self.dashes
        ]
        formatted.extend(s[:-1] for s in format_exception(exception))
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


class HierarchicalResult(SimpleResult, StreamResult):
    dashes = '-' * 70

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary = []

    def context_started(self, context):
        super().context_started(context)
        self.current_summary = [context.name]

    def context_ended(self, context):
        super().context_ended(context)
        context_vm = self.view_models[-1]
        if context_vm.assertion_failures or context_vm.assertion_errors:
            self.summary.extend(self.current_summary)

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        context_vm = self.view_models[-1]
        formatted_exc = ''.join(context_vm.error_summary).split('\n')[:-1]
        self.current_summary.extend('  ' + s for s in formatted_exc)
        self.summary.extend(self.current_summary)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        context_vm = self.view_models[-1]
        assertion_vm = context_vm.assertions[-1]
        formatted_exc = ''.join(assertion_vm.error_summary).split('\n')[:-1]
        self.current_summary.append('  FAIL: ' + assertion_vm.name)
        self.current_summary.extend('    ' + s for s in formatted_exc)

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        context_vm = self.view_models[-1]
        assertion_vm = context_vm.assertions[-1]
        formatted_exc = ''.join(assertion_vm.error_summary).split('\n')[:-1]
        self.current_summary.append('  ERROR: ' + assertion_vm.name)
        self.current_summary.extend('    ' + s for s in formatted_exc)

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.summarise()

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
        num_ctx = len(self.view_models)
        num_ass = len(self.assertions)
        msg = "{}, {}".format(pluralise("context", num_ctx), pluralise("assertion", num_ass))
        return msg

    def failure_numbers(self):
        num_ctx = len(self.view_models)
        num_ass = len(self.assertions)
        num_ctx_err = len(self.context_errors)
        num_fail = len(self.assertion_failures)
        num_err = len(self.assertion_errors)
        msg =  "{}, {}: {} failed, {}".format(pluralise("context", num_ctx),
           pluralise("assertion", num_ass),
           num_fail,
           pluralise("error", num_err + num_ctx_err))
        return msg


class TimedResult(StreamResult):
    def suite_started(self, suite):
        super().suite_started(suite)
        self.start_time = datetime.datetime.now()

    def suite_ended(self, suite):
        self.end_time = datetime.datetime.now()
        super().suite_ended(suite)

        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


class CapturingResult(SummarisingResult):
    def context_started(self, context):
        super().context_started(context)
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer

    def context_ended(self, context):
        sys.stdout = self.real_stdout
        super().context_ended(context)

    def context_errored(self, context, exception):
        sys.stdout = self.real_stdout
        super().context_errored(context, exception)
        self.append_buffer_to_summary()

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        self.append_buffer_to_summary()

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        self.append_buffer_to_summary()

    def append_buffer_to_summary(self):
        if self.buffer.getvalue():
            self.summary.append("-------------------- >> begin captured stdout << ---------------------")
            self.summary.append(self.buffer.getvalue()[:-1])
            self.summary.append("--------------------- >> end captured stdout << ----------------------")


# class HierarchicalCapturingResult(HierarchicalResult):
#     def context_started(self, context):
#         super().context_started(context)
#         self.real_stdout = sys.stdout
#         self.buffer = StringIO()
#         sys.stdout = self.buffer

#     def context_ended(self, context):
#         sys.stdout = self.real_stdout
#         super().context_ended(context)

#     def context_errored(self, context, exception):
#         sys.stdout = self.real_stdout
#         super().context_errored(context, exception)
#         self.append_buffer_to_summary()

#     def assertion_failed(self, assertion, exception):
#         super().assertion_failed(assertion, exception)
#         self.append_buffer_to_summary()

#     def assertion_errored(self, assertion, exception):
#         super().assertion_errored(assertion, exception)
#         self.append_buffer_to_summary()

#     def append_buffer_to_summary(self):
#         if self.buffer.getvalue():
#             self.summary.append("-------------------- >> begin captured stdout << ---------------------")
#             self.summary.append(self.buffer.getvalue()[:-1])
#             self.summary.append("--------------------- >> end captured stdout << ----------------------")


class NonCapturingCLIResult(DotsResult, TimedResult, SummarisingResult):
    pass


class CLIResult(CapturingResult, NonCapturingCLIResult):
    pass


class HierarchicalCLIResult(DotsResult, TimedResult, HierarchicalResult):
    pass


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    exception.__traceback__ = None
    return ret
