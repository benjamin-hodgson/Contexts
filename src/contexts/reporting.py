import datetime
import re
import sys
import traceback
from io import StringIO


class Reporter(object):
    @property
    def failed(self):
        return True

    def suite_started(self, suite):
        """Called at the beginning of a test run"""

    def suite_ended(self, suite):
        """Called at the end of a test run"""

    def unexpected_error(self, exception):
        """Called when an error occurs outside of a Context or Assertion"""

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
        self.name = make_readable(context.name)
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
    def last_assertion(self):
        return self.assertions[-1]

    @property
    def assertion_failures(self):
        return [a for a in self.assertions if a.status == "failed"]
    @property
    def assertion_errors(self):
        return [a for a in self.assertions if a.status == "errored"]


class AssertionViewModel(object):
    def __init__(self, assertion, status="passed", exception=None):
        self.name = make_readable(assertion.name)
        self.status = status
        self.error_summary = None
        if exception is not None:
            self.error_summary = format_exception(exception)


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
        self.view_models.append(ContextViewModel(context))

    def context_errored(self, context, exception):
        self.current_context.exception = exception
        super().context_errored(context, exception)

    def assertion_passed(self, assertion):
        assertion_vm = AssertionViewModel(assertion)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_passed(assertion)

    def assertion_failed(self, assertion, exception):
        assertion_vm = AssertionViewModel(assertion, "failed", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_failed(assertion, exception)

    def assertion_errored(self, assertion, exception):
        assertion_vm = AssertionViewModel(assertion, "errored", exception)
        self.current_context.assertions.append(assertion_vm)
        super().assertion_errored(assertion, exception)

    def unexpected_error(self, exception):
        self.unexpected_errors.append(format_exception(exception))
        super().unexpected_error(exception)


class StreamReporter(Reporter):
    def __init__(self, stream=sys.stderr):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)


class DotsReporter(StreamReporter):
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


class SummarisingReporter(SimpleReporter, StreamReporter):
    dashes = '-' * 70

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary = []
        self.current_summary = None
        self.current_indent = ''

    def context_started(self, context):
        super().context_started(context)
        self.current_summary = [self.current_context.name]
        self.indent()

    def context_ended(self, context):
        super().context_ended(context)
        if self.current_context.assertion_failures or self.current_context.assertion_errors:
            self.add_current_context_to_summary()
        self.dedent()
        self.current_summary = None

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        formatted_exc = self.current_context.error_summary
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
        assertion_vm = self.current_context.assertions[-1]
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
        num_ctx = len(self.view_models)
        num_ass = len(self.assertions)
        return "{}, {}".format(
            pluralise("context", num_ctx),
            pluralise("assertion", num_ass))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", len(self.view_models)),
            pluralise("assertion", len(self.assertions)),
            len(self.assertion_failures),
            pluralise("error", len(self.assertion_errors) + len(self.context_errors) + len(self.unexpected_errors)))


class TeamCityReporter(StreamReporter, SimpleReporter):
    def suite_started(self, suite):
        super().suite_started(suite)
        msg = self.teamcity_format("##teamcity[testSuiteStarted name='{}']", "contexts")
        self._print(msg)
    def suite_ended(self, suite):
        super().suite_ended(suite)
        msg = self.teamcity_format("##teamcity[testSuiteFinished name='{}']", "contexts")
        self._print(msg)

    def context_started(self, context):
        super().context_started(context)
        self.context_name_prefix = self.current_context.name + ' -> '
    def context_ended(self, context):
        super().context_ended(context)
        self.context_name_prefix = ''
    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        self.context_name_prefix = ''
        context_vm = self.current_context
        msg1 = self.teamcity_format("##teamcity[testStarted name='{}']", context_vm.name)
        self._print(msg1)
        msg2 = self.teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", self.current_context.name, str(exception), '\n'.join(context_vm.error_summary))
        self._print(msg2)
        msg3 = self.teamcity_format("##teamcity[testFinished name='{}']", context_vm.name)
        self._print(msg3)

    def assertion_started(self, assertion):
        super().assertion_started(assertion)
        assertion_name = make_readable(assertion.name)
        msg = self.teamcity_format("##teamcity[testStarted name='{}']", self.context_name_prefix + assertion_name)
        self._print(msg)
    def assertion_passed(self, assertion):
        super().assertion_passed(assertion)
        assertion_vm = self.current_context.last_assertion
        msg = self.teamcity_format("##teamcity[testFinished name='{}']", self.context_name_prefix + assertion_vm.name)
        self._print(msg)
    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        assertion_vm = self.current_context.last_assertion
        msg1 = self.teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", self.context_name_prefix + assertion_vm.name, str(exception), '\n'.join(assertion_vm.error_summary))
        self._print(msg1)
        msg2 = self.teamcity_format("##teamcity[testFinished name='{}']", self.context_name_prefix + assertion_vm.name)
        self._print(msg2)
    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        assertion_vm = self.current_context.last_assertion
        msg1 = self.teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", self.context_name_prefix + assertion_vm.name, str(exception), '\n'.join(assertion_vm.error_summary))
        self._print(msg1)
        msg2 = self.teamcity_format("##teamcity[testFinished name='{}']", self.context_name_prefix + assertion_vm.name)
        self._print(msg2)

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        self.context_name_prefix = ''
        context_vm = self.current_context
        msg1 = self.teamcity_format("##teamcity[testStarted name='Test error']")
        self._print(msg1)
        msg2 = self.teamcity_format("##teamcity[testFailed name='Test error' message='{}' details='{}']", str(exception), '\n'.join(self.unexpected_errors[-1]))
        self._print(msg2)
        msg3 = self.teamcity_format("##teamcity[testFinished name='Test error']")
        self._print(msg3)

    @classmethod
    def teamcity_format(cls, format_string, *args):
        strings = [cls.teamcity_escape(arg) for arg in args]
        return format_string.format(*strings)

    @classmethod
    def teamcity_escape(cls, string):
        return string.replace("|", "||").replace('\n', '|n').replace("'", "|'").replace("\r", "|r").replace("[", "|[").replace("]", "|]")


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


class TimedReporter(StreamReporter):
    def suite_started(self, suite):
        super().suite_started(suite)
        self.start_time = datetime.datetime.now()

    def suite_ended(self, suite):
        self.end_time = datetime.datetime.now()
        super().suite_ended(suite)

        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


class NonCapturingCLIReporter(DotsReporter, TimedReporter, SummarisingReporter):
    pass


class CapturingCLIReporter(NonCapturingCLIReporter, StdOutCapturingReporter):
    pass


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    exception.__traceback__ = None
    return ''.join(ret).strip().split('\n')


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string

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
