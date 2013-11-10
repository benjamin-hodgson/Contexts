import inspect
import itertools
from contextlib import contextmanager
from . import errors
from . import finders


class Assertion(object):
    def __init__(self, func, name):
        self.func = func
        self.name = name

    def run(self, test_data, reporter_runner):
        with reporter_runner.run_assertion(self):
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

    def run_assertions(self, reporter_runner):
        for assertion in self.assertions:
            assertion.run(self.test_data, reporter_runner)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.test_data)

    def run(self, reporter_runner):
        with reporter_runner.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions(reporter_runner)
            finally:
                self.run_teardown()


class Suite(object):
    def __init__(self, classes):
        self.classes = list(classes)

    def run(self, reporter_runner):
        with reporter_runner.run_suite(self):
            for cls in self.classes:
                self.run_class(cls, reporter_runner)

    def run_class(self, cls, reporter_runner):
        with reporter_runner.run_class(cls):
            for context in build_contexts_for_class(cls):
                context.run(reporter_runner)



def build_contexts_for_class(cls):
    instances = instantiate(cls)
    contexts = []
    for instance in instances:
        context = wrap_instance_in_context(instance)
        contexts.append(context)
    return contexts


def instantiate(cls):
    examples_method = finders.find_examples_method(cls)
    test_data_iterable = examples_method()
    specs = []
    if test_data_iterable is not None:
        for test_data in test_data_iterable:
            inst = cls()
            inst._contexts_test_data = test_data
            specs.append(inst)
        instances = specs
    else:
        instances = [cls()]
    return instances


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


class ReporterRunner(object):
    def __init__(self, reporter):
        self.reporter = reporter

    @contextmanager
    def run_suite(self, suite):
        self.reporter.suite_started(suite)
        yield
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
