class Assertion(object):
    def __init__(self, func, full_name):
        self.ran = False
        self.func = func
        self.name = full_name
        self.exception = None

    def run(self):
        self.ran = True
        try:
            self.func()
        except AssertionError as e:
            self.exception = e
        except Exception as e:
            self.exception = e


class Context(object):
    def __init__(self, setups, actions, assertions, teardowns):
        self.ran = False
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

    def run_assertions(self):
        for assertion in self.assertions:
            assertion.run()

    def run_teardown(self):
        for teardown in self.teardowns:
            teardown()

    @property
    def result(self):
        return Result([self])

    def run(self):
        self.ran = True
        try:
            self.run_setup()
            self.run_action()
            self.run_assertions()
            self.run_teardown()
        except Exception as e:
            for assertion in self.assertions:
                assertion.exception = e


class Suite(object):
    def __init__(self, contexts):
        self.contexts = contexts
        self.result = Result(self.contexts)

    def run(self):
        for ctx in self.contexts:
            ctx.run()


class Result(object):
    def __init__(self, contexts=None):
        self.contexts = contexts if contexts is not None else []

    @property
    def assertions(self):
        return [a for c in self.contexts for a in c.assertions]

    @property
    def failures(self):
        return [a for a in self.assertions if isinstance(a.exception, AssertionError)]

    @property
    def errors(self):
        pred = lambda a: (isinstance(a.exception, Exception) and not
                          isinstance(a.exception, AssertionError))
        return [a for a in self.assertions if pred(a)]

    def __add__(self, other):
        contexts = self.contexts + other.contexts
        return Result(contexts)

    def __eq__(self, other):
        return self.contexts == other.contexts
