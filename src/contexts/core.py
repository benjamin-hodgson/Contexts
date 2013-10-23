import traceback
from contextlib import contextmanager


class Assertion(object):
    def __init__(self, func, name):
        self.func = func
        self.name = name

    def run(self, result_runner):
        with result_runner.run_assertion(self):
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

    def run_assertions(self, result_runner):
        for assertion in self.assertions:
            assertion.run(result_runner)

    def run_teardown(self):
        for teardown in self.teardowns:
            teardown()

    def run(self, result_runner):
        with result_runner.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions(result_runner)
            finally:
                self.run_teardown()


class Suite(object):
    def __init__(self, contexts):
        self.contexts = contexts

    def run(self, result_runner):
        with result_runner.run_suite(self):
            for ctx in self.contexts:
                ctx.run(result_runner)


class ResultRunner(object):
    def __init__(self, result):
        self.result = result

    @contextmanager
    def run_suite(self, suite):
        self.result.suite_started(suite)
        yield
        self.result.suite_ended(suite)

    @contextmanager
    def run_context(self, context):
        self.result.context_started(context)
        try:
            yield
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None  # to prevent memory leaks caused by keeping tracebacks around
            self.result.context_errored(context, e, tb)
        else:
            self.result.context_ended(context)

    @contextmanager
    def run_assertion(self, assertion):
        self.result.assertion_started(assertion)
        try:
            yield
        except AssertionError as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None
            self.result.assertion_failed(assertion, e, tb)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            e.__traceback__ = None
            self.result.assertion_errored(assertion, e, tb)
        else:
            self.result.assertion_passed(assertion)
