from contexts.plugin_interface import CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts.plugins.decorators import DecoratorBasedIdentifier, spec, context, examples, setup, action, assertion, teardown
from contexts import catch


class WhenMarkingAClassAsASpec:
    def context(self):
        @spec
        class LovelyClass(object):
            pass
        self.cls = LovelyClass
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self):
        self.result = self.identifier.identify_class(self.cls)

    @assertion
    def it_should_identify_it_as_a_context(self):
        assert self.result is CONTEXT

class WhenMarkingAClassAsAContext:
    def context(self):
        @context
        class LovelyClass(object):
            pass
        self.cls = LovelyClass
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self):
        self.result = self.identifier.identify_class(self.cls)

    @assertion
    def it_should_identify_it_as_a_context(self):
        assert self.result is CONTEXT


class WhenMarkingAMethodAsExamples:
    def context(self):
        class C:
            @classmethod
            @examples
            def innocuous_method(cls):
                pass
        self.method = C.innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    @assertion
    def it_should_identify_it_as_examples(self):
        assert self.result is EXAMPLES


class WhenMarkingAMethodAsSetup:
    def context(self):
        @setup
        def innocuous_method(self):
            pass
        self.method = innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    def it_should_identify_it_as_setup(self):
        assert self.result is SETUP


class WhenMarkingAMethodAsAction:
    def context(self):
        @action
        def innocuous_method(self):
            pass
        self.method = innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    def it_should_identify_it_as_action(self):
        assert self.result is ACTION


class WhenMarkingAMethodAsAnAssertion:
    def context(self):
        @assertion
        def innocuous_method(self):
            pass
        self.method = innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    def it_should_identify_it_as_an_assertion(self):
        assert self.result is ASSERTION


class WhenMarkingAMethodAsATeardown:
    def context(self):
        @teardown
        def innocuous_method(self):
            pass
        self.method = innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    def it_should_identify_it_as_teardown(self):
        assert self.result is TEARDOWN


class WhenMarkingAMethodAsTwoThings:
    @classmethod
    def examples(cls):
        yield examples, setup
        yield setup, action
        yield action, assertion
        yield assertion, teardown
        yield teardown, examples

    def given_an_attempt_to_use_multiple_decorators(self, decorator1, decorator2):
        def throwing_func():
            @decorator1
            @decorator2
            def a_function():
                pass
        self.throwing_func = throwing_func

    def when_we_try_to_use_the_decorators(self):
        self.exception = catch(self.throwing_func)

    def it_should_throw_a_ValueError(self):
        assert isinstance(self.exception, ValueError)
