from contexts.plugin_interface import CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts.plugins.identifiers import DecoratorBasedIdentifier
import contexts


class WhenMarkingAClassAsASpec:
    def context(self):
        @contexts.spec
        class LovelyClass(object):
            pass
        self.cls = LovelyClass
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self):
        self.result = self.identifier.identify_class(self.cls)

    @contexts.assertion
    def it_should_identify_it_as_a_context(self):
        assert self.result is CONTEXT

class WhenMarkingAClassAsAContext:
    def context(self):
        @contexts.context
        class LovelyClass(object):
            pass
        self.cls = LovelyClass
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self):
        self.result = self.identifier.identify_class(self.cls)

    @contexts.assertion
    def it_should_identify_it_as_a_context(self):
        assert self.result is CONTEXT


class WhenMarkingAMethodAsExamples:
    def context(self):
        class C:
            @classmethod
            @contexts.examples
            def innocuous_method(cls):
                pass
        self.method = C.innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    @contexts.assertion
    def it_should_identify_it_as_examples(self):
        assert self.result is EXAMPLES


class WhenMarkingAMethodAsSetup:
    def context(self):
        @contexts.setup
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
        @contexts.action
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
        @contexts.assertion
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
        @contexts.teardown
        def innocuous_method(self):
            pass
        self.method = innocuous_method
        self.identifier = DecoratorBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self):
        self.result = self.identifier.identify_method(self.method)

    def it_should_identify_it_as_teardown(self):
        assert self.result is TEARDOWN
