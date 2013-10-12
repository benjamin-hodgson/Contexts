import traceback


def freeze_traceback(e):
    e.tb = traceback.extract_tb(e.__traceback__)
    e.__traceback__ = None


class Assertion(object):
    def __init__(self, func, full_name):
        self.func = func
        self.name = full_name

    def run(self, result):
        result.add_assertion(self)
        try:
            self.func()
        except AssertionError as e:
            freeze_traceback(e)
            result.assertion_failed(self, e)
        except Exception as e:
            freeze_traceback(e)
            result.assertion_errored(self, e)


class Context(object):
    def __init__(self, setups, actions, assertions, teardowns):
        self.setups = setups
        self.actions = actions
        self.assertions = assertions
        self.teardowns = teardowns

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
        result.add_context(self)
        try:
            self.run_setup()
            self.run_action()
            self.run_assertions(result)
            self.run_teardown()
        except Exception as e:
            freeze_traceback(e)
            result.context_errored(self, e)


class Suite(object):
    def __init__(self, contexts):
        self.contexts = contexts

    def run(self, result):
        for ctx in self.contexts:
            ctx.run(result)

