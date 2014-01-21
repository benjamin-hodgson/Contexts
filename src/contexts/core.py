import inspect
import itertools
import os
import types
from contextlib import contextmanager
from . import discovery
from . import errors
from . import finders
from .tools import NO_EXAMPLE
from . import plugins


class TestRun(object):
    def __init__(self, source, plugin_notifier):
        self.source = source
        self.plugin_notifier = plugin_notifier

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
            return [self.import_from_file(self.source)]
        if isinstance(self.source, str) and os.path.isdir(self.source):
            specifications = discovery.module_specs(self.source)
            modules = []
            for module_spec in specifications:
                with self.plugin_notifier.importing(module_spec):
                    modules.append(self.import_module(*module_spec))
            return modules

        # self.source is a class

        module = types.ModuleType("contexts_module")
        # use a hard-coded name that the finder will recognise (needs a better fix)
        module.Spec = self.source
        return [module]

    def import_from_file(self, file_path):
        folder = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        module_name = os.path.splitext(filename)[0]
        return self.import_module(folder, module_name)

    def import_module(self, dir_path, module_name):
        return self.plugin_notifier.call_plugins('import_module', dir_path, module_name)


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
                test_class = TestClass(cls, self.plugin_notifier)
                test_class.run()


class TestClass(object):
    def __init__(self, cls, plugin_notifier):
        self.cls = cls
        self.plugin_notifier = plugin_notifier

        self.examples_method = None
        self.unbound_setups = []
        self.unbound_actions = []  # fixme: this should just be a single function, not a list
        self.unbound_assertions = []
        self.unbound_teardowns = []

        for superclass in reversed(inspect.getmro(cls)):
            class_examples = None
            class_setup = None
            class_action = None
            class_teardown = None

            for name, val in superclass.__dict__.items():
                if isinstance(val, classmethod):
                    val = getattr(superclass, name)

                if callable(val) and not isprivate(name):
                    response = self.plugin_notifier.call_plugins("identify_method", val)
                else:
                    continue

                if response is plugins.EXAMPLES:
                    if class_examples is not None:
                        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
                        msg += class_examples.__name__ + ", " + name
                        raise errors.TooManySpecialMethodsError(msg)
                    self.examples_method = class_examples = val
                elif response is plugins.SETUP:
                    if class_setup is not None:
                        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
                        msg += class_setup.__name__ + ", " + name
                        raise errors.TooManySpecialMethodsError(msg)
                    class_setup = val
                    self.unbound_setups.append(val)
                elif response is plugins.ACTION and superclass is cls:
                    if class_action is not None:
                        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
                        msg += class_action.__name__ + ", " + name
                        raise errors.TooManySpecialMethodsError(msg)
                    class_action = val
                    self.unbound_actions.append(val)
                elif response is plugins.ASSERTION and superclass is cls:
                    self.unbound_assertions.append(val)
                elif response is plugins.TEARDOWN:
                    if class_teardown is not None:
                        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
                        msg += class_teardown.__name__ + ", " + name
                        raise errors.TooManySpecialMethodsError(msg)
                    class_teardown = val
                    self.unbound_teardowns.append(val)
        self.unbound_teardowns.reverse()

        finder = finders.UnboundMethodFinder(self.cls)
        if self.examples_method is None:
            self.examples_method = finder.find_examples_method()
        self.unbound_setups.extend(finder.find_setups())
        self.unbound_actions.extend(finder.find_actions())
        self.unbound_assertions.extend(finder.find_assertions())
        self.unbound_teardowns.extend(finder.find_teardowns())

        assert_no_ambiguous_methods(self.unbound_setups, self.unbound_actions, self.unbound_assertions, self.unbound_teardowns)

    def run(self):
        with self.plugin_notifier.run_class(self):
            for example in self.get_examples():
                context = Context(
                    self.cls(), example,
                    self.unbound_setups,
                    self.unbound_actions,
                    self.unbound_assertions,
                    self.unbound_teardowns,
                    self.plugin_notifier
                )
                context.run()

    def get_examples(self):
        examples = self.examples_method()
        return examples if examples is not None else [NO_EXAMPLE]


def isprivate(name):
    return name.startswith('_')


def assert_no_ambiguous_methods(*iterables):
    for a, b in itertools.combinations((set(i) for i in iterables), 2):
        overlap = a & b
        if overlap:
            msg = "The following methods are ambiguously named:\n"
            msg += '\n'.join([func.__qualname__ for func in overlap])
            raise errors.MethodNamingError(msg)


class Context(object):
    def __init__(self, instance, example,
                 unbound_setups, unbound_actions, unbound_assertions, unbound_teardowns,
                 plugin_notifier):
        self.plugin_notifier = plugin_notifier
        self.instance = instance
        self.example = example
        self.name = instance.__class__.__name__

        self.setups = bind_methods(unbound_setups, self.instance)
        self.actions = bind_methods(unbound_actions, self.instance)
        self.assertions = bind_methods(unbound_assertions, self.instance)
        self.teardowns = bind_methods(unbound_teardowns, self.instance)

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


def bind_methods(methods, instance):
    return [types.MethodType(func, instance) for func in methods]


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
    def run_class(self, test_class):
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
