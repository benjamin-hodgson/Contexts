import io
import re
from datetime import datetime, timedelta
from lxml import etree

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

    @property
    def passed(self):
        return not(self.failure or self.errors)


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
        return '\n' + '\n'.join(format_exception(self.failure or self.error)) + '\n'

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



ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

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

    def write_test_suites(self):
        total_tests = sum([len(suite) for suite in self.suites])
        return etree.Element(
            "testsuites",
            tests=str(total_tests),
            errors=str(self.suites.errors),
            failures=str(self.suites.failures),
            time="{0:.2f}".format(self.suites.time.total_seconds()),
        )

    def write_test_suite(self, suites_el, suite):
        suite_el = etree.SubElement(
            suites_el,
            "testsuite",
            name=suite.name,
            tests=str(len(suite)),
            errors=str(suite.errors),
            failures=str(suite.failures),
            time="{0:.2f}".format(suite.time.total_seconds()),
        )
        for test in suite.children:
            self.write_test(suite_el, test)

    def write_test(self, suite_el, test):
        testcase_el = etree.SubElement(
            suite_el,
            "testcase",
            name=test.name,
            time="{0:.2f}".format(test.time.total_seconds())
        )

        if test.passed:
            return
        tag = 'failure' if test.failure else 'error'
        failure_el = etree.SubElement(
            testcase_el,
            tag,
            type=tag,
            message=ANSI_ESCAPE.sub('', test.msg)
        )
        failure_el.text = etree.CDATA(ANSI_ESCAPE.sub('', test.nfo))


    def test_run_ended(self):
        self.suites.stop()
        suites_el = self.write_test_suites()
        for suite in self.suites:
            self.write_test_suite(suites_el, suite)

        with io.open(self.path, 'wb') as f:
            etree.ElementTree(suites_el).write(f, pretty_print=True)
