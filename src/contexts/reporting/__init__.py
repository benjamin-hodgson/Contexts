from contextlib import contextmanager


class ReporterNotifier(object):
    def __init__(self, reporter):
        self.reporter = reporter

    @contextmanager
    def run_suite(self, suite):
        self.reporter.suite_started(suite)
        try:
            yield
        except Exception as e:
            self.reporter.unexpected_error(e)
        self.reporter.suite_ended(suite)

    @contextmanager
    def run_context(self, context):
        self.reporter.context_started(context)
        try:
            yield
        except Exception as e:
            self.reporter.context_errored(context, e)
        else:
            self.reporter.context_ended(context)

    @contextmanager
    def run_assertion(self, assertion):
        self.reporter.assertion_started(assertion)
        try:
            yield
        except AssertionError as e:
            self.reporter.assertion_failed(assertion, e)
        except Exception as e:
            self.reporter.assertion_errored(assertion, e)
        else:
            self.reporter.assertion_passed(assertion)

    @contextmanager
    def run_class(self, cls):
        try:
            yield
        except Exception as e:
            self.reporter.unexpected_error(e)

    @contextmanager
    def importing(self, module_spec):
        try:
            yield
        except Exception as e:
            self.reporter.unexpected_error(e)


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
