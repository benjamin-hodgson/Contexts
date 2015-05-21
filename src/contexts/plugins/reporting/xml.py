from datetime import datetime, timedelta
import io
import xml.etree.ElementTree as ET

from . import context_name, format_exception, make_readable
from ...plugin_interface import NO_EXAMPLE


class Result:

    def __init__(self, name):
        self.name = name
        self.time = timedelta(0)
        self.started = datetime.now()
        self.children = []

    def stop(self):
        self.time = datetime.now() - self.started

    def add_child(self, result):
        self.children.append(result)

    @property
    def failures(self):
        failures = 0
        for test in self.children:
            failures = failures + test.failures
        return failures

    @property
    def errors(self):
        errors = 0
        for test in self.children:
            errors = errors + test.errors
        return errors

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return self.children.__iter__()

    def next(self):
        return self.children.next()


class AssertionResult(Result):

    def __init__(self, name):
        super(AssertionResult, self).__init__(name)
        self.failure = None
        self.error = None

    @property
    def msg(self):
        return str(self.failure or self.error)

    @property
    def nfo(self):
        return format_exception(self.failure or self.error)

    @property
    def failures(self):
        if self.failure:
            return 1
        return 0

    @property
    def errors(self):
        if self.error:
            return 1
        return 0


class XmlReporter:

    def __init__(self):
        self.suites = Result("Test suites")
        self.path = None

    def initialise(self, args, environ):
        if(args and args.xml_path):
            self.path = args.xml_path
            return True
        return False

    def setup_parser(self, parser):
        parser.add_argument('--xml',
                            action='store',
                            dest='xml_path',
                            default=None,
                            help='Path for XML output'
                            )

    def context_started(self, cls, example=NO_EXAMPLE):
        name = context_name(cls.__name__, example)
        ctx = self.ctx = Result(name)
        self.suites.add_child(ctx)

    def context_ended(self, cls, example=NO_EXAMPLE):
        self.ctx.stop()

    def assertion_started(self, func):
        self.test = AssertionResult(make_readable(func.__name__))
        self.ctx.add_child(self.test)

    def assertion_passed(self, func):
        self.test.stop()

    def assertion_failed(self, func, exception):
        self.test.stop()
        self.test.failure = exception

    def assertion_errored(self, func, exception):
        self.test.stop()
        self.test.error = exception

    def write_test_suites(self, builder):
        total_tests = sum([len(suite) for suite in self.suites])
        builder.start("testsuites", {
            "tests": str(total_tests),
            "errors": str(self.suites.errors),
            "failures": str(self.suites.failures),
            "time": "{0:.2f}".format(self.suites.time.total_seconds())

        })

    def write_test_suite(self, builder, suite):
        builder.start("testsuite", {
            "name": suite.name,
            "tests": str(len(suite)),
            "errors": str(suite.errors),
            "failures": str(suite.failures),
            "time": "{0:.2f}".format(suite.time.total_seconds())
        })
        for test in suite.children:
            self.write_test(builder, test)

    def write_test(self, builder, test):
        builder.start("testcase", {
            "name": test.name,
            "time": "{0:.2f}".format(test.time.total_seconds())
        })

        if(test.failure):
            builder.start("failure", {
                "type": "failure",
                "message": test.msg
            })
            builder.data(test.nfo)
            builder.end("failure")
        elif(test.error):
            builder.start("error", {
                "type": "error",
                "message": test.msg
            })
            builder.data(test.nfo)
            builder.end("error")

        builder.end('testcase')

    def end_test_suite(self, builder):
        builder.end('testsuite')

    def end_test_suites(self, builder):
        builder.end('testsuites')

    def test_run_ended(self):
        self.suites.stop()
        builder = ET.TreeBuilder()
        self.write_test_suites(builder)
        for suite in self.suites:
            self.write_test_suite(builder, suite)
            self.end_test_suite(builder)
        self.end_test_suites(builder)

        el = ET.ElementTree(element=builder.close())
        with io.open(self.path, 'wb') as f:
            el.write(f)
