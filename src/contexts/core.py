from contextlib import contextmanager
import traceback


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
            self.run_setup()
            self.run_action()
            self.run_assertions(result)
            self.run_teardown()


class Suite(object):
    def __init__(self, contexts):
        self.contexts = contexts

    def run(self, result):
        for ctx in self.contexts:
            ctx.run(result)


class Result(object):
    def __init__(self):
        self.contexts = []
        self.assertions = []
        self.context_errors = []
        self.assertion_errors = []
        self.assertion_failures = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures

    @contextmanager
    def run_context(self, context):
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

    def context_ran(self, context):
        self.contexts.append(context)

    def context_errored(self, context, exception, extracted_traceback):
        self.contexts.append(context)
        self.context_errors.append((context, exception, extracted_traceback))

    def assertion_passed(self, assertion):
        self.assertions.append(assertion)

    def assertion_errored(self, assertion, exception, extracted_traceback):
        self.assertions.append(assertion)
        self.assertion_errors.append((assertion, exception, extracted_traceback))

    def assertion_failed(self, assertion, exception, extracted_traceback):
        self.assertions.append(assertion)
        self.assertion_failures.append((assertion, exception, extracted_traceback))
