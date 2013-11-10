import inspect
import itertools
from contextlib import contextmanager
from . import errors
from . import finders


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
    def __init__(self, classes):
        self.classes = classes

    def run(self, result_runner):
        with result_runner.run_suite(self):
            instances = itertools.chain.from_iterable(instantiate(cls) for cls in self.classes)
            self.contexts = [wrap_instance_in_context(instance) for instance in instances]
            for ctx in self.contexts:
                ctx.run(result_runner)


def wrap_instance_in_context(instance):
    finder = finders.MethodFinder(instance)
    setups, actions, assertions, teardowns = finder.find_special_methods()
    assert_no_ambiguous_methods(setups, actions, assertions, teardowns)
    wrapped_assertions = [Assertion(f, f.__name__) for f in assertions]
    return Context(setups,
                   actions,
                   wrapped_assertions,
                   teardowns,
                   instance._contexts_test_data if hasattr(instance, '_contexts_test_data') else None,
                   instance.__class__.__name__)


def instantiate(cls):
    """
    Return a list of instances of cls.
    If cls has an 'examples' method, run it and return an instance for each example.
    Otherwise, return a list containing one instance of the class, plain.
    """
    examples_method = finders.find_examples_method(cls)
    test_data_iterable = examples_method()
    specs = []
    if test_data_iterable is not None:
        for test_data in test_data_iterable:
            inst = cls()
            inst._contexts_test_data = test_data
            specs.append(inst)
        return specs
    return [cls()]


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
    sig = inspect.signature(func)
    if test_data is not None and sig.parameters:
        func(test_data)
    else:
        func()


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
