import abc
import traceback
from contextlib import contextmanager


class Assertion(object):
    def __init__(self, func, name):
        self.func = func
        self.name = name

    def run(self, result):
        with result.run_assertion(self):
            self.func()


class Context(object):
    def __init__(self, setups, actions, assertions, teardowns, name):
        self.setups = setups
        self.actions = actions
        self.assertions = assertions
        self.teardowns = teardowns
        self.name = name

    def run_setup(self):
        for setup in self.setups:
            setup()

    def run_action(self):
        for action in self.actions:
            action()

    def run_assertions(self, result):
        for assertion in self.assertions:
            assertion.run(result)

    def run_teardown(self):
        for teardown in self.teardowns:
            teardown()

    def run(self, result):
        with result.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions(result)
            finally:
                self.run_teardown()


class Suite(object):
    def __init__(self, contexts):
        self.contexts = contexts

    def run(self, result):
        with result.run_suite(self):
            for ctx in self.contexts:
                ctx.run(result)


class Result(metaclass=abc.ABCMeta):
    @contextmanager
    def run_suite(self, suite):
        self.suite_started(suite)
        yield
        self.suite_ended(suite)

    @contextmanager
    def run_context(self, context):
        self.context_started(context)
        try:
            yield
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None  # to prevent memory leaks caused by keeping tracebacks around
            self.context_errored(context, e, tb)
        else:
            self.context_ran(context)

    @contextmanager
    def run_assertion(self, assertion):
        self.assertion_started(assertion)
        try:
            yield
        except AssertionError as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None
            self.assertion_failed(assertion, e, tb)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None
            self.assertion_errored(assertion, e, tb)
        else:
            self.assertion_passed(assertion)

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

    def context_ran(self, context):
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
