import sys
from io import StringIO
from . import shared


class TeamCityReporter(shared.StreamReporter):
    def suite_started(self, name):
        super().suite_started(name)
        self.teamcity_print("testSuiteStarted", name=name)

    def suite_ended(self, name):
        super().suite_ended(name)
        self.teamcity_print("testSuiteFinished", name=name)

    def context_started(self, name, example):
        super().context_started(name, example)
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout_buffer, self.stderr_buffer = StringIO(), StringIO()
        self.context_name_prefix = shared.context_name(name, example) + ' -> '

    def context_ended(self, name, example):
        super().context_ended(name, example)
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr
        self.context_name_prefix = ''

    def context_errored(self, name, example, exception):
        super().context_errored(name, example, exception)
        self.context_name_prefix = ''
        name = shared.context_name(name, example)
        error_summary = shared.format_exception(exception)

        self.teamcity_print("testStarted", name=name)
        self.output_buffers(name)
        self.teamcity_print(
            "testFailed",
            name=name,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=name)

        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr
        self.failed = True

    def assertion_started(self, name):
        super().assertion_started(name)
        readable_name = self.context_name_prefix + shared.make_readable(name)
        self.teamcity_print("testStarted", name=readable_name)

    def assertion_passed(self, name):
        super().assertion_passed(name)
        name = self.context_name_prefix + shared.make_readable(name)
        self.output_buffers(name)
        self.teamcity_print("testFinished", name=name)

    def assertion_failed(self, name, exception):
        super().assertion_failed(name, exception)
        name = self.context_name_prefix + shared.make_readable(name)
        error_summary = shared.format_exception(exception)

        self.output_buffers(name)
        self.teamcity_print(
            "testFailed",
            name=name,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=name)
        self.failed = True

    def assertion_errored(self, name, exception):
        super().assertion_errored(name, exception)
        name = self.context_name_prefix + shared.make_readable(name)
        error_summary = shared.format_exception(exception)

        self.output_buffers(name)
        self.teamcity_print(
            "testFailed",
            name=name,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=name)
        self.failed = True

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        error_summary = shared.format_exception(exception)
        self.context_name_prefix = ''
        self.teamcity_print("testStarted", name='Test error')
        self.teamcity_print("testFailed", name='Test error', message=error_summary[-1], details='\n'.join(error_summary))
        self.teamcity_print("testFinished", name='Test error')
        self.failed = True

    def output_buffers(self, name):
        if self.stdout_buffer.getvalue():
            self.teamcity_print(
                "testStdOut",
                name=name,
                out=self.stdout_buffer.getvalue()
            )
        if self.stderr_buffer.getvalue():
            self.teamcity_print(
                "testStdErr",
                name=name,
                out=self.stderr_buffer.getvalue()
            )

    def teamcity_print(self, msgName, **kwargs):
        msg = ' '.join(teamcity_format("{}='{}'", k, v) for k, v in kwargs.items())
        self._print("##teamcity[{} {}]".format(teamcity_format(msgName), msg))


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