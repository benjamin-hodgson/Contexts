import types
from contexts.plugin_interface import CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from . import NameBasedIdentifier


class DecoratorBasedIdentifier(object):
    decorated_items = {
        "contexts": set(),
        "examples": set(),
        "setups": set(),
        "actions": set(),
        "assertions": set(),
        "teardowns": set()
    }

    @classmethod
    def locate(self):
        return (None, NameBasedIdentifier)

    def initialise(self, args, env):
        return True

    def identify_class(self, cls):
        if cls in self.decorated_items["contexts"]:
            return CONTEXT

    def identify_method(self, method):
        if isinstance(method, types.MethodType):
            # robin hack, prince of hacks.
            # this is to make it work with classmethods (such as examples)
            method = method.__func__

        if method in self.decorated_items["examples"]:
            return EXAMPLES
        if method in self.decorated_items["setups"]:
            return SETUP
        if method in self.decorated_items["actions"]:
            return ACTION
        if method in self.decorated_items["assertions"]:
            return ASSERTION
        if method in self.decorated_items["teardowns"]:
            return TEARDOWN

    def __eq__(self, other):
        return type(self) == type(other)


def spec(cls):
    """
    Class decorator. Marks a class as a test class.
    """
    assert_not_multiple_decorators(cls, "contexts")
    DecoratorBasedIdentifier.decorated_items["contexts"].add(cls)
    return cls

context = scenario = spec


def setup(func):
    """
    Decorator. Marks a method as a setup method.
    """
    assert_not_multiple_decorators(func, "setups")
    DecoratorBasedIdentifier.decorated_items["setups"].add(func)
    return func


def action(func):
    """
    Decorator. Marks a method as an action method.
    """
    assert_not_multiple_decorators(func, "actions")
    DecoratorBasedIdentifier.decorated_items["actions"].add(func)
    return func


def assertion(func):
    """
    Decorator. Marks a method as an assertion method.
    """
    assert_not_multiple_decorators(func, "assertions")
    DecoratorBasedIdentifier.decorated_items["assertions"].add(func)
    return func


def teardown(func):
    """
    Decorator. Marks a method as a teardown method.
    """
    assert_not_multiple_decorators(func, "teardowns")
    DecoratorBasedIdentifier.decorated_items["teardowns"].add(func)
    return func


def examples(func):
    """
    Decorator. Marks a method as an examples method.
    """
    assert_not_multiple_decorators(func, "examples")
    DecoratorBasedIdentifier.decorated_items["examples"].add(func)
    return func


def assert_not_multiple_decorators(item, decorator_type):
    if any(item in s for k, s in DecoratorBasedIdentifier.decorated_items.items() if k != decorator_type):
        raise ValueError("Function {} has more than one decorator")
