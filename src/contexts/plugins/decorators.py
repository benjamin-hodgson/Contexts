import types
from ..plugin_interface import CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN


class DecoratorBasedIdentifier(object):
    decorated_items = {
        "contexts": set(),
        "examples": set(),
        "setups": set(),
        "actions": set(),
        "assertions": set(),
        "teardowns": set(),
    }

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



def setup(func):
    """
    Decorator. Marks a method as a setup method.
    """
    DecoratorBasedIdentifier.decorated_items["setups"].add(func)
    return func


def action(func):
    """
    Decorator. Marks a method as an action method.
    """
    DecoratorBasedIdentifier.decorated_items["actions"].add(func)
    return func


def assertion(func):
    """
    Decorator. Marks a method as an assertion method.
    """
    DecoratorBasedIdentifier.decorated_items["assertions"].add(func)
    return func


def teardown(func):
    """
    Decorator. Marks a method as a teardown method.
    """
    DecoratorBasedIdentifier.decorated_items["teardowns"].add(func)
    return func


def examples(func):
    """
    Decorator. Marks a method as an examples method.
    """
    DecoratorBasedIdentifier.decorated_items["examples"].add(func)
    return func


def spec(cls):
    """
    Class decorator. Marks a class as a test class.
    """
    DecoratorBasedIdentifier.decorated_items["contexts"].add(cls)
    return cls

context = spec
