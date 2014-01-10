import inspect
import itertools
import os
import random
import types
from contextlib import contextmanager
from . import discovery
from . import errors
from . import finders
from . import importing


class TestRun(object):
    def __init__(self, source, rewriting, config):
        self.source = source
        self.rewriting = rewriting
        self.config = config

    def run(self, reporter_notifier):
        with reporter_notifier.run_test_run(self):
            modules = self.get_modules(reporter_notifier)
            if self.config.shuffle:
                random.shuffle(modules)
            for module in modules:
                suite = Suite(module, self.config)
                suite.run(reporter_notifier)

    def get_modules(self, reporter_notifier):
        if isinstance(self.source, types.ModuleType):
            return [self.source]
        if isinstance(self.source, str) and os.path.isfile(self.source):
            return [importing.import_from_file(self.source, self.rewriting)]
        if isinstance(self.source, str) and os.path.isdir(self.source):
            specifications = discovery.module_specs(self.source)
            modules = []
            for module_spec in specifications:
                with reporter_notifier.importing(module_spec):
                    modules.append(importing.import_module(*module_spec, rewriting=self.rewriting))
            return modules

        # if we got here, self.source is a class
        module = types.ModuleType("contexts_module")
        setattr(module, "Spec", self.source)
        return [module]


class Suite(object):
    def __init__(self, module, config):
        self.module = module
        self.name = self.module.__name__
        self.config = config

    def run(self, reporter_notifier):
        with reporter_notifier.run_suite(self):
            found_classes = list(finders.find_specs_in_module(self.module))
            if self.config.shuffle:
                random.shuffle(found_classes)
            for cls in found_classes:
                self.run_class(cls, reporter_notifier)

    def run_class(self, cls, reporter_notifier):
        with reporter_notifier.run_class(cls):
            for example in get_examples(cls):
                context = Context(cls(), example, self.config)
                context.run(reporter_notifier)


def get_examples(cls):
    examples_method = finders.find_examples_method(cls)
    examples = examples_method()
    return examples if examples is not None else [_NullExample()]


class _NullExample(object):
    null_example = True


class Context(object):
    def __init__(self, instance, example, config):
        finder = finders.MethodFinder(instance)
        setups, actions, assertions, teardowns = finder.find_special_methods()
        assert_no_ambiguous_methods(setups, actions, assertions, teardowns)
        self.instance = instance
        self.setups = setups
        self.actions = actions
        self.assertions = [Assertion(f) for f in assertions]
        self.teardowns = teardowns
        self.example = example
        self.name = instance.__class__.__name__
        self.config = config

        if self.config.shuffle:
            random.shuffle(self.assertions)

    def run_setup(self):
        for setup in self.setups:
            run_with_test_data(setup, self.example)

    def run_action(self):
        for action in self.actions:
            run_with_test_data(action, self.example)

    def run_assertions(self, reporter_notifier):
        for assertion in self.assertions:
            assertion.run(self.example, reporter_notifier)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.example)

    def run(self, reporter_notifier):
        if not self.assertions:
            return
        with reporter_notifier.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions(reporter_notifier)
            finally:
                self.run_teardown()

def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)


class Assertion(object):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def run(self, test_data, reporter_notifier):
        with reporter_notifier.run_assertion(self):
            run_with_test_data(self.func, test_data)


def run_with_test_data(func, test_data):
    sig = inspect.signature(func)
    if not isinstance(test_data, _NullExample) and sig.parameters:
        if isinstance(test_data, tuple) and len(sig.parameters) == len(test_data):
            func(*test_data)
        else:
            func(test_data)
    else:
        func()


class ReporterNotifier(object):
    def __init__(self, *reporters):
        self.reporters = []
        for reporter in reporters:
            self.reporters.append(reporter)

    @property
    def failed(self):
        return any(r.failed for r in self.reporters if hasattr(r, 'failed'))

    def call_reporters(self, method, *args):
        for reporter in self.reporters:
            getattr(reporter, method)(*args)

    @contextmanager
    def run_test_run(self, test_run):
        self.call_reporters("test_run_started", test_run)
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)
        self.call_reporters("test_run_ended", test_run)

    @contextmanager
    def run_suite(self, suite):
        self.call_reporters("suite_started", suite)
        yield
        self.call_reporters("suite_ended", suite)

    @contextmanager
    def run_context(self, context):
        self.call_reporters("context_started", context)
        try:
            yield
        except Exception as e:
            self.call_reporters("context_errored", context, e)
        else:
            self.call_reporters("context_ended", context)

    @contextmanager
    def run_assertion(self, assertion):
        self.call_reporters("assertion_started", assertion)
        try:
            yield
        except AssertionError as e:
            self.call_reporters("assertion_failed", assertion, e)
        except Exception as e:
            self.call_reporters("assertion_errored", assertion, e)
        else:
            self.call_reporters("assertion_passed", assertion)

    @contextmanager
    def run_class(self, cls):
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)

    @contextmanager
    def importing(self, module_spec):
        try:
            yield
        except Exception as e:
            self.call_reporters("unexpected_error", e)
