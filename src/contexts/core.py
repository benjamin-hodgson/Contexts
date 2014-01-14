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
from .tools import NO_EXAMPLE


class TestRun(object):
    def __init__(self, source, rewriting, plugin_notifier):
        self.source = source
        self.plugin_notifier = plugin_notifier
        self.importer = importing.Importer(rewriting, self.plugin_notifier)

    def run(self):
        with self.plugin_notifier.run_test_run(self):
            modules = self.get_modules()
            self.plugin_notifier.call_plugins('process_module_list', modules)
            for module in modules:
                suite = Suite(module, self.plugin_notifier)
                suite.run()

    def get_modules(self):
        if isinstance(self.source, types.ModuleType):
            return [self.source]
        if isinstance(self.source, str) and os.path.isfile(self.source):
            return [self.importer.import_from_file(self.source)]
        if isinstance(self.source, str) and os.path.isdir(self.source):
            specifications = discovery.module_specs(self.source)
            modules = []
            for module_spec in specifications:
                with self.plugin_notifier.importing(module_spec):
                    modules.append(self.importer.import_module(*module_spec))
            return modules

        # self.source is a class

        module = types.ModuleType("contexts_module")
        # use a hard-coded name that the finder will recognise (needs a better fix)
        module.Spec = self.source
        return [module]


class Suite(object):
    def __init__(self, module, plugin_notifier):
        self.module = module
        self.name = self.module.__name__
        self.plugin_notifier = plugin_notifier

    def run(self):
        with self.plugin_notifier.run_suite(self):
            found_classes = list(finders.find_specs_in_module(self.module))
            self.plugin_notifier.call_plugins('process_class_list', found_classes)
            for cls in found_classes:
                self.run_class(cls)

    def run_class(self, cls):
        with self.plugin_notifier.run_class(cls):
            for example in get_examples(cls):
                context = Context(cls(), example, self.plugin_notifier)
                context.run()


def get_examples(cls):
    examples_method = finders.find_examples_method(cls)
    examples = examples_method()
    return examples if examples is not None else [NO_EXAMPLE]


class _NullExample(object):
    null_example = True


class Context(object):
    def __init__(self, instance, example, plugin_notifier):
        self.plugin_notifier = plugin_notifier

        finder = finders.MethodFinder(instance)
        setups, actions, assertions, teardowns = finder.find_special_methods()
        assert_no_ambiguous_methods(setups, actions, assertions, teardowns)

        self.instance = instance
        self.setups = setups
        self.actions = actions
        self.assertions = assertions
        self.teardowns = teardowns
        self.example = example
        self.name = instance.__class__.__name__

    def run_setup(self):
        for setup in self.setups:
            run_with_test_data(setup, self.example)

    def run_action(self):
        for action in self.actions:
            run_with_test_data(action, self.example)

    def run_assertions(self):
        for assertion in self.assertions:
            assertion.run(self.example)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.example)

    def run(self):
        self.plugin_notifier.call_plugins('process_assertion_list', self.assertions)
        self.assertions = [Assertion(f, self.plugin_notifier) for f in self.assertions]

        if not self.assertions:
            return
        with self.plugin_notifier.run_context(self):
            try:
                self.run_setup()
                self.run_action()
                self.run_assertions()
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
    def __init__(self, func, plugin_notifier):
        self.func = func
        self.name = func.__name__
        self.plugin_notifier = plugin_notifier

    def run(self, test_data):
        with self.plugin_notifier.run_assertion(self):
            run_with_test_data(self.func, test_data)


def run_with_test_data(func, test_data):
    sig = inspect.signature(func)
    if test_data is not NO_EXAMPLE and sig.parameters:
        if isinstance(test_data, tuple) and len(sig.parameters) == len(test_data):
            func(*test_data)
        else:
            func(test_data)
    else:
        func()


class PluginNotifier(object):
    def __init__(self, plugins):
        self.plugins = plugins

    @property
    def failed(self):
        return any(r.failed for r in self.plugins if hasattr(r, 'failed'))

    @contextmanager
    def run_test_run(self, test_run):
        self.call_plugins("test_run_started")
        try:
            yield
        except Exception as e:
            self.call_plugins("unexpected_error", e)
        self.call_plugins("test_run_ended")

    @contextmanager
    def importing(self, module_spec):
        try:
            yield
        except Exception as e:
            self.call_plugins("unexpected_error", e)

    @contextmanager
    def run_suite(self, suite):
        self.call_plugins("suite_started", suite.name)
        yield
        self.call_plugins("suite_ended", suite.name)

    @contextmanager
    def run_class(self, cls):
        try:
            yield
        except Exception as e:
            self.call_plugins("unexpected_error", e)

    @contextmanager
    def run_context(self, context):
        self.call_plugins("context_started", context.name, context.example)
        try:
            yield
        except Exception as e:
            self.call_plugins("context_errored", context.name, context.example, e)
        else:
            self.call_plugins("context_ended", context.name, context.example)

    @contextmanager
    def run_assertion(self, assertion):
        self.call_plugins("assertion_started", assertion.name)
        try:
            yield
        except AssertionError as e:
            self.call_plugins("assertion_failed", assertion.name, e)
        except Exception as e:
            self.call_plugins("assertion_errored", assertion.name, e)
        else:
            self.call_plugins("assertion_passed", assertion.name)

    def call_plugins(self, method, *args):
        for plugin in self.plugins:
            reply = getattr(plugin, method, lambda *_: None)(*args)
            if reply is not None:
                return reply
