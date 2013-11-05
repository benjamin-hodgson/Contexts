from contextlib import contextmanager


class Assertion(object):
    def __init__(self, func, name):
        self.func = func
        self.name = name

    def run(self, test_data, result_runner):
        with result_runner.run_assertion(self):
            run_with_test_data(self.func, test_data)


class Context(object):
    def __init__(self, setups, actions, assertions, teardowns, test_data, name):
        self.setups = setups
        self.actions = actions
        self.assertions = assertions
        self.teardowns = teardowns
        self.test_data = test_data
        self.name = name

    def run_setup(self):
        for setup in self.setups:
            run_with_test_data(setup, self.test_data)

    def run_action(self):
        for action in self.actions:
            run_with_test_data(action, self.test_data)

    def run_assertions(self, result_runner):
        for assertion in self.assertions:
            assertion.run(self.test_data, result_runner)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.test_data)

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
            self.result.context_errored(context, e)
        else:
            self.result.context_ended(context)

    @contextmanager
    def run_assertion(self, assertion):
        self.result.assertion_started(assertion)
        try:
            yield
        except AssertionError as e:
            self.result.assertion_failed(assertion, e)
        except Exception as e:
            self.result.assertion_errored(assertion, e)
        else:
            self.result.assertion_passed(assertion)

def run_with_test_data(func, test_data):
    if test_data is not None:
        func(test_data)
    else:
        func()
