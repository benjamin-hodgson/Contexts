from ..plugin_interface import CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN


class DecoratorBasedIdentifier(object):
    def identify_class(self, cls):
        if not hasattr(cls, "_contexts_role"):
            return None

        d = {
            "Spec": CONTEXT
        }
        return d[cls._contexts_role]

    def identify_method(self, method):
        if not hasattr(method, "_contexts_role"):
            return None

        d = {
            "examples": EXAMPLES,
            "establish": SETUP,
            "because": ACTION,
            "should": ASSERTION,
            "cleanup": TEARDOWN
        }
        return d[method._contexts_role]

    def __eq__(self, other):
        return type(self) == type(other)



def setup(func):
    """
    Decorator. Marks a method as a setup method.
    """
    func._contexts_role = "establish"
    return func


def action(func):
    """
    Decorator. Marks a method as an action method.
    """
    func._contexts_role = "because"
    return func


def assertion(func):
    """
    Decorator. Marks a method as an assertion method.
    """
    func._contexts_role = "should"
    return func


def teardown(func):
    """
    Decorator. Marks a method as a teardown method.
    """
    func._contexts_role = "cleanup"
    return func


def examples(func):
    """
    Decorator. Marks a method as an examples method.
    """
    func._contexts_role = "examples"
    return func


def spec(cls):
    """
    Class decorator. Marks a class as a test class.
    """
    cls._contexts_role = "Spec"
    return cls

context = spec
