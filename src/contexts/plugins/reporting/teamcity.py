import sys
from io import StringIO
from . import cli
from . import StreamReporter, context_name, format_exception, make_readable


class TeamCityReporter(StreamReporter):
    @classmethod
    def locate(cls):
        return (None, cli.DotsReporter)

    def setup_parser(self, parser):
        parser.add_argument('--teamcity',
            action='store_true',
            dest='teamcity',
            default=False,
            help="Enable teamcity test reporting.")

    def initialise(self, args, env):
        return args.teamcity or ('TEAMCITY_VERSION' in env)

    def test_run_started(self):
        return True

    def test_run_ended(self):
        return True

    def test_class_started(self, cls):
        self.teamcity_print("testClassStarted", name=cls.__name__)
        return True

    def test_class_ended(self, cls):
        self.teamcity_print("testClassFinished", name=cls.__name__)
        return True

    def test_class_errored(self, cls, exception):
        error_summary = format_exception(exception)

        self.teamcity_print("testStarted", name=cls.__name__)
        self.teamcity_print(
            "testFailed",
            name=cls.__name__,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=cls.__name__)
        self.teamcity_print("testClassFinished", name=cls.__name__)
        return True

    def suite_started(self, name):
        self.teamcity_print("testSuiteStarted", name=name)
        return True

    def suite_ended(self, name):
        self.teamcity_print("testSuiteFinished", name=name)
        return True

    def context_started(self, cls, example):
        self.real_stdout, self.real_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout_buffer, self.stderr_buffer = StringIO(), StringIO()
        self.context_name_prefix = context_name(cls.__name__, example) + ' -> '
        return True

    def context_ended(self, cls, example):
        sys.stdout, sys.stderr = self.real_stdout, self.real_stderr
        self.context_name_prefix = ''
        return True

    def context_errored(self, cls, example, exception):
        self.context_name_prefix = ''
        name = context_name(cls.__name__, example)
        error_summary = format_exception(exception)

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
        return True

    def assertion_started(self, name):
        readable_name = self.context_name_prefix + make_readable(name)
        self.teamcity_print("testStarted", name=readable_name)
        return True

    def assertion_passed(self, name):
        name = self.context_name_prefix + make_readable(name)
        self.output_buffers(name)
        self.teamcity_print("testFinished", name=name)
        return True

    def assertion_failed(self, name, exception):
        name = self.context_name_prefix + make_readable(name)
        error_summary = format_exception(exception)

        self.output_buffers(name)
        self.teamcity_print(
            "testFailed",
            name=name,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=name)
        self.failed = True
        return True

    def assertion_errored(self, name, exception):
        name = self.context_name_prefix + make_readable(name)
        error_summary = format_exception(exception)

        self.output_buffers(name)
        self.teamcity_print(
            "testFailed",
            name=name,
            message=error_summary[-1],
            details='\n'.join(error_summary)
        )
        self.teamcity_print("testFinished", name=name)
        self.failed = True
        return True

    def unexpected_error(self, exception):
        error_summary = format_exception(exception)
        self.context_name_prefix = ''
        self.teamcity_print("testStarted", name='Test error')
        self.teamcity_print("testFailed", name='Test error', message=error_summary[-1], details='\n'.join(error_summary))
        self.teamcity_print("testFinished", name='Test error')
        self.failed = True
        return True

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
