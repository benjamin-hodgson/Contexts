import inspect
import itertools
import os
import types
from contextlib import contextmanager
from . import discovery
from . import errors
from . import finders


def run_with_test_data(func, test_data):
    sig = inspect.signature(func)
    if test_data is not None and sig.parameters:
        func(test_data)
    else:
        func()


class Assertion(object):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def run(self, test_data, reporter_notifier):
        with reporter_notifier.run_assertion(self):
            run_with_test_data(self.func, test_data)


class Context(object):
    def __init__(self, instance):
        finder = finders.MethodFinder(instance)
        setups, actions, assertions, teardowns = finder.find_special_methods()
        assert_no_ambiguous_methods(setups, actions, assertions, teardowns)
        self.instance = instance
        self.setups = setups
        self.actions = actions
        self.assertions = [Assertion(f) for f in assertions]
        self.teardowns = teardowns
        self.test_data = instance._contexts_test_data
        self.name = instance.__class__.__name__

    def run_setup(self):
        for setup in self.setups:
            run_with_test_data(setup, self.test_data)

    def run_action(self):
        for action in self.actions:
            run_with_test_data(action, self.test_data)

    def run_assertions(self, reporter_notifier):
        for assertion in self.assertions:
            assertion.run(self.test_data, reporter_notifier)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.test_data)

    def run(self, reporter_notifier):
        with reporter_notifier.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions(reporter_notifier)
            finally:
                self.run_teardown()


class Suite(object):
    def __init__(self, source):
        self.source = source

    def run(self, reporter_notifier):
        with reporter_notifier.run_suite(self):
            for cls in self.get_classes(reporter_notifier):
                self.run_class(cls, reporter_notifier)

    def run_class(self, cls, reporter_notifier):
        with reporter_notifier.run_class(cls):
            for example in get_examples(cls):
                context = build_context(cls, example)
                context.run(reporter_notifier)

    def get_classes(self, reporter_notifier):
        if isinstance(self.source, str) and os.path.isfile(self.source):
            module = discovery.import_from_file(self.source)
            classes = finders.find_specs_in_module(module)
        elif isinstance(self.source, types.ModuleType):
            classes = finders.find_specs_in_module(self.source)
        elif isinstance(self.source, str) and os.path.isdir(self.source):
            module_specs = discovery.find_modules(self.source)
            classes = []
            for module_spec in module_specs:
                with reporter_notifier.importing(module_spec):
                    module = discovery.load_module(*module_spec)
                    classes.extend(finders.find_specs_in_module(module))
        else:
            classes = list(self.source)
        return classes


def get_examples(cls):
    examples_method = finders.find_examples_method(cls)
    test_data_iterable = examples_method()
    return test_data_iterable if test_data_iterable is not None else [None]


def build_context(cls, test_data):
    instance = cls()
    instance._contexts_test_data = test_data
    return Context(instance)


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


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)
