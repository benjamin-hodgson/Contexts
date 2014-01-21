import contexts
from contexts.plugins import EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts.plugins.identifiers import NameBasedIdentifier


class WhenIdentifyingAnExamplesMethod:
    @classmethod
    def examples_of_legal_examples_names(self):
        def method_with_example_in_the_name():
            pass
        yield method_with_example_in_the_name
        def method_with_data_in_the_name(self):
            pass
        yield method_with_data_in_the_name

    def establish(self):
        self.finder = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.finder.identify_method(method)

    @contexts.assertion
    def it_should_identify_it_as_examples(self):
        assert self.result is EXAMPLES


class WhenIdentifyingASetupMethod:
    @classmethod
    def examples_of_legal_setup_names(self):
        def method_with_establish_in_the_name():
            pass
        yield method_with_establish_in_the_name
        def method_with_context_in_the_name(self):
            pass
        yield method_with_context_in_the_name
        def method_with_given_in_the_name(self):
            pass
        yield method_with_given_in_the_name

    def establish(self):
        self.finder = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.finder.identify_method(method)

    def it_should_identify_it_as_setup(self):
        assert self.result is SETUP


class WhenIdentifyingAnActionMethod:
    @classmethod
    def examples_of_legal_action_names(self):
        def method_with_because_in_the_name():
            pass
        yield method_with_because_in_the_name
        def method_with_when_in_the_name(self):
            pass
        yield method_with_when_in_the_name
        def method_with_since_in_the_name(self):
            pass
        yield method_with_since_in_the_name
        def method_with_after_in_the_name(self):
            pass
        yield method_with_after_in_the_name

    def establish(self):
        self.finder = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.finder.identify_method(method)

    def it_should_identify_it_as_an_action(self):
        assert self.result is ACTION


class WhenIdentifyingAnAssertionMethod:
    @classmethod
    def examples_of_legal_assertion_names(self):
        def method_with_it_in_the_name():
            pass
        yield method_with_it_in_the_name
        def method_with_should_in_the_name(self):
            pass
        yield method_with_should_in_the_name
        def method_with_then_in_the_name(self):
            pass
        yield method_with_then_in_the_name
        def method_with_must_in_the_name(self):
            pass
        yield method_with_must_in_the_name
        def method_with_will_in_the_name(self):
            pass
        yield method_with_will_in_the_name

    def establish(self):
        self.finder = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.finder.identify_method(method)

    def it_should_identify_it_as_an_assertion(self):
        assert self.result is ASSERTION


class WhenIdentifyingATeardownMethod:
    @classmethod
    def examples_of_legal_teardown_names(self):
        def method_with_cleanup_in_the_name():
            pass
        yield method_with_cleanup_in_the_name

    def establish(self):
        self.finder = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.finder.identify_method(method)

    def it_should_identify_it_as_a_teardown(self):
        assert self.result is TEARDOWN
