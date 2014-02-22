import inspect
import os
import types
from contextlib import contextmanager
from . import discovery
from . import errors
from .plugin_interface import PluginInterface, TEST_FOLDER, CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN, NO_EXAMPLE


class TestRun(object):
    def __init__(self, source, plugin_composite):
        self.source = source
        self.plugin_composite = plugin_composite
        self.exception_handler = ExceptionHandler(self.plugin_composite)

    def run(self):
        with self.exception_handler.run_test_run(self):
            if isinstance(self.source, type):
                test_class = TestClass(self.source, self.plugin_composite)
                test_class.run()
            else:
                modules = self.import_modules()
                self.plugin_composite.process_module_list(modules)
                for module in modules:
                    suite = Suite(module, self.plugin_composite)
                    suite.run()

    def import_modules(self):
        if isinstance(self.source, types.ModuleType):
            return [self.source]
        if os.path.isfile(self.source):
            folder, filename = os.path.split(self.source)
            importer = discovery.create_importer(folder, self.plugin_composite, self.exception_handler)
            module = importer.import_file(filename)
            if module is None:
                return []
            return [module]
        if os.path.isdir(self.source):
            return self.import_modules_from_folder(self.source)

    def import_modules_from_folder(self, directory):
        module_list = discovery.ModuleList(self.plugin_composite, self.exception_handler)
        for folder, dirnames, _ in os.walk(directory):
            self.remove_non_test_folders(folder, dirnames)
            importer = discovery.create_importer(folder, self.plugin_composite, self.exception_handler)
            for folder, filename in importer.module_specs():
                module_list.add(folder, filename)
        return module_list.modules

    def remove_non_test_folders(self, parent, dirnames):
        replacement = []
        for dirname in dirnames:
            full_path = os.path.realpath(os.path.join(parent, dirname))
            reply = self.plugin_composite.identify_folder(full_path)
            if reply is TEST_FOLDER:
                replacement.append(dirname)
        dirnames[:] = replacement


class Suite(object):
    def __init__(self, module, plugin_composite):
        self.module = module
        self.name = self.module.__name__
        self.plugin_composite = plugin_composite
        self.exception_handler = ExceptionHandler(self.plugin_composite)

        self.classes = self.get_classes()
        self.plugin_composite.process_class_list(self.classes)

    def run(self):
        with self.exception_handler.run_suite(self):
            for cls in self.classes:
                test_class = TestClass(cls, self.plugin_composite)
                test_class.run()

    def get_classes(self):
        classes = []
        for name, cls in inspect.getmembers(self.module, inspect.isclass):
            response = self.plugin_composite.identify_class(cls)
            if response is CONTEXT:
                classes.append(cls)
        return classes


class TestClass(object):
    def __init__(self, cls, plugin_composite):
        self.cls = cls
        self.plugin_composite = plugin_composite
        self.exception_handler = ExceptionHandler(self.plugin_composite)

        self.examples_method = None
        self.unbound_setups = []
        self.unbound_action = None
        self.unbound_assertions = []
        self.unbound_teardowns = []

        for superclass in reversed(inspect.getmro(cls)):
            bottom_of_tree = (superclass is cls)
            self.load_special_methods_from_class(superclass, bottom_of_tree)
        self.unbound_teardowns.reverse()

        if self.examples_method is None:
            self.examples_method = lambda: None
        if self.unbound_action is None:
            self.unbound_action = lambda self: None

    def run(self):
        if not self.unbound_assertions:
            return

        with self.exception_handler.run_class(self):
            for example in self.get_examples():
                context = Context(
                    self.cls(), example,
                    self.unbound_setups,
                    self.unbound_action,
                    self.unbound_assertions,
                    self.unbound_teardowns,
                    self.plugin_composite
                )
                context.run()

    def get_examples(self):
        examples = self.examples_method()
        return examples if examples is not None else [NO_EXAMPLE]

    def load_special_methods_from_class(self, cls, bottom_of_tree):
        # there should be one of each of these per class,
        # but there may be more than one in the inheritance tree
        class_setup = None
        class_teardown = None

        for name in cls.__dict__:
            val = getattr(cls, name)

            if callable(val) and not isprivate(name):
                response = self.plugin_composite.identify_method(val)

                if response is EXAMPLES and bottom_of_tree:
                    assert_not_too_many_special_methods(self.examples_method, cls, val)
                    self.examples_method = val
                elif response is SETUP:
                    assert_not_too_many_special_methods(class_setup, cls, val)
                    class_setup = val
                    self.unbound_setups.append(val)
                elif response is ACTION and bottom_of_tree:
                    assert_not_too_many_special_methods(self.unbound_action, cls, val)
                    self.unbound_action = val
                elif response is ASSERTION and bottom_of_tree:
                    self.unbound_assertions.append(val)
                elif response is TEARDOWN:
                    assert_not_too_many_special_methods(class_teardown, cls, val)
                    class_teardown = val
                    self.unbound_teardowns.append(val)


def isprivate(name):
    return name.startswith('_')


def assert_not_too_many_special_methods(previously_found, cls, just_found):
    if previously_found is not None:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += previously_found.__name__ + ", " + just_found.__name__
        raise errors.TooManySpecialMethodsError(msg)


class Context(object):
    def __init__(self, instance, example,
                 unbound_setups, unbound_action, unbound_assertions, unbound_teardowns,
                 plugin_composite):
        self.plugin_composite = plugin_composite
        self.exception_handler = ExceptionHandler(self.plugin_composite)

        self.instance = instance
        self.example = example
        self.name = instance.__class__.__name__

        self.setups = bind_methods(unbound_setups, self.instance)
        self.action = types.MethodType(unbound_action, self.instance)
        self.assertions = bind_methods(unbound_assertions, self.instance)
        self.teardowns = bind_methods(unbound_teardowns, self.instance)

    def run(self):
        self.plugin_composite.process_assertion_list(self.assertions)
        self.assertions = [Assertion(f, self.plugin_composite) for f in self.assertions]
        with self.exception_handler.run_context(self):
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
        run_with_test_data(self.action, self.example)

    def run_assertions(self):
        for assertion in self.assertions:
            assertion.run(self.example)

    def run_teardown(self):
        for teardown in self.teardowns:
            run_with_test_data(teardown, self.example)


def bind_methods(methods, instance):
    return [types.MethodType(func, instance) for func in methods]


class Assertion(object):
    def __init__(self, func, plugin_composite):
        self.func = func
        self.name = func.__name__
        self.plugin_composite = plugin_composite
        self.exception_handler = ExceptionHandler(self.plugin_composite)

    def run(self, test_data):
        with self.exception_handler.run_assertion(self):
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


class ExceptionHandler(object):
    def __init__(self, plugin_composite):
        self.plugin_composite = plugin_composite

    @contextmanager
    def run_test_run(self, test_run):
        self.plugin_composite.test_run_started()
        try:
            yield
        except Exception as e:
            self.plugin_composite.unexpected_error(e)
        self.plugin_composite.test_run_ended()

    @contextmanager
    def importing(self, folder, filename):
        try:
            yield
        except Exception as e:
            self.plugin_composite.unexpected_error(e)

    @contextmanager
    def run_suite(self, suite):
        self.plugin_composite.suite_started(suite.name)
        yield
        self.plugin_composite.suite_ended(suite.name)

    @contextmanager
    def run_class(self, test_class):
        self.plugin_composite.test_class_started(test_class.cls)
        try:
            yield
        except Exception as e:
            self.plugin_composite.test_class_errored(test_class.cls, e)
        else:
            self.plugin_composite.test_class_ended(test_class.cls)

    @contextmanager
    def run_context(self, context):
        self.plugin_composite.context_started(context.name, context.example)
        try:
            yield
        except Exception as e:
            self.plugin_composite.context_errored(context.name, context.example, e)
        else:
            self.plugin_composite.context_ended(context.name, context.example)

    @contextmanager
    def run_assertion(self, assertion):
        self.plugin_composite.assertion_started(assertion.name)
        try:
            yield
        except AssertionError as e:
            self.plugin_composite.assertion_failed(assertion.name, e)
        except Exception as e:
            self.plugin_composite.assertion_errored(assertion.name, e)
        else:
            self.plugin_composite.assertion_passed(assertion.name)


class PluginComposite(object):
    def __init__(self, plugins):
        self.plugins = plugins

    def __getattr__(self, name):
        # not expecting this to happen
        if name not in PluginInterface.__dict__:
            raise AttributeError('The method {} is not part of the plugin interface'.format(name))

        def plugin_method(*args, **kwargs):
            for plugin in self.plugins:
                reply = getattr(plugin, name, lambda *_: None)(*args)
                if reply is not None:
                    return reply
        return plugin_method
