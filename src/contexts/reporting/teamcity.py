import sys
from io import StringIO
from . import shared


class TeamCityReporter(shared.StreamReporter, shared.SimpleReporter):
    def suite_started(self, suite):
        super().suite_started(suite)
        self.teamcity_print("testSuiteStarted", name="contexts")

    def suite_ended(self, suite):
        super().suite_ended(suite)
        self.teamcity_print("testSuiteFinished", name="contexts")

    def context_started(self, context):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout_buffer, self.stderr_buffer = StringIO(), StringIO()
        super().context_started(context)
        self.context_name_prefix = self.current_context.name + ' -> '

    def context_ended(self, context):
        super().context_ended(context)
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr
        self.context_name_prefix = ''

    def context_errored(self, context, exception):
        super().context_errored(context, exception)
        self.context_name_prefix = ''
        context_vm = self.view_models[context]
        self.teamcity_print("testStarted", name=context_vm.name)
        self.output_buffers(context_vm.name)
        msg2 = teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", context_vm.name, str(exception), '\n'.join(context_vm.error_summary))
        self._print(msg2)
        self.teamcity_print("testFinished", name=context_vm.name)
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr

    def assertion_started(self, assertion):
        super().assertion_started(assertion)
        assertion_name = shared.make_readable(assertion.name)
        self.teamcity_print("testStarted", name=self.context_name_prefix+assertion_name)

    def assertion_passed(self, assertion):
        super().assertion_passed(assertion)
        assertion_vm = self.current_context.current_assertion
        name = self.context_name_prefix + assertion_vm.name
        self.output_buffers(name)
        self.teamcity_print("testFinished", name=name)

    def assertion_failed(self, assertion, exception):
        super().assertion_failed(assertion, exception)
        assertion_vm = self.current_context.current_assertion
        name = self.context_name_prefix + assertion_vm.name
        self.output_buffers(name)
        msg = teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", self.context_name_prefix + assertion_vm.name, str(exception), '\n'.join(assertion_vm.error_summary))
        self._print(msg)
        self.teamcity_print("testFinished", name=name)

    def assertion_errored(self, assertion, exception):
        super().assertion_errored(assertion, exception)
        assertion_vm = self.current_context.current_assertion
        name = self.context_name_prefix + assertion_vm.name
        self.output_buffers(name)
        msg = teamcity_format("##teamcity[testFailed name='{}' message='{}' details='{}']", self.context_name_prefix + assertion_vm.name, str(exception), '\n'.join(assertion_vm.error_summary))
        self._print(msg)
        self.teamcity_print("testFinished", name=name)

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        self.context_name_prefix = ''
        self.teamcity_print("testStarted", name='Test error')
        msg2 = teamcity_format("##teamcity[testFailed name='Test error' message='{}' details='{}']", str(exception), '\n'.join(self.unexpected_errors[-1]))
        self._print(msg2)
        self.teamcity_print("testFinished", name='Test error')

    def teamcity_print(self, msgName, **kwargs):
        msg = ' '.join(teamcity_format("{}='{}'", k, v) for k, v in kwargs.items())
        self._print("##teamcity[{} {}]".format(teamcity_format(msgName), msg))

    def output_buffers(self, name):
        if self.stdout_buffer.getvalue():
            msg = teamcity_format("##teamcity[testStdOut name='{}' out='{}']", name, self.stdout_buffer.getvalue())
            self._print(msg)
        if self.stderr_buffer.getvalue():
            msg = teamcity_format("##teamcity[testStdErr name='{}' out='{}']", name, self.stderr_buffer.getvalue())
            self._print(msg)


def teamcity_format(format_string, *args):
    strings = [escape(arg) for arg in args]
    return format_string.format(*strings)


def escape(string):
    return ''.join([escape_char(char) for char in string])


def escape_char(char):
    if char == '\n':
        return '|n'
    if char == '\r':
        return '|r'
    if char in "'[]|":
        return '|' + char
    ordinal = ord(char)
    if ordinal >= 128:
        return '|0x{:04x}'.format(ordinal)
    return char
