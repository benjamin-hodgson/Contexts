import os.path
import contexts
from contexts.plugins import TEST_FOLDER, CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts.plugins.identifiers import NameBasedIdentifier


class WhenIdentifyingAFolder:
    @classmethod
    def examples_of_legal_test_folder_names(self):
        yield 'test'
        yield os.path.join('a_folder', 'tests')
        yield 'spec'
        yield os.path.join('another_folder', 'specs')

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self, folder):
        self.result = self.identifier.identify_folder(folder)

    def it_should_identify_it_as_a_test_folder(self):
        assert self.result is TEST_FOLDER


class WhenIdentifyingANonTestFolder:
    @classmethod
    def examples_of_non_test_folder_names(self):
        yield 'innocent_folder'
        yield os.path.join('tests', 'subfolder')
        yield os.path.join('spec', 'another_subfolder')

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self, folder):
        self.result = self.identifier.identify_folder(folder)

    def it_should_not_point_any_fingers(self):
        assert self.result is None


class WhenIdentifyingAClass:
    @classmethod
    def examples_of_legal_test_class_names(self):
        class ClassWithWhenInTheName:
            pass
        yield ClassWithWhenInTheName
        class ClassWithSpecInTheName:
            pass
        yield ClassWithSpecInTheName

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self, cls):
        self.result = self.identifier.identify_class(cls)

    @contexts.assertion
    def it_should_identify_it_as_a_context(self):
        assert self.result is CONTEXT


class WhenIdentifyingANormalClass:
    @classmethod
    def examples_of_legal_test_class_names(self):
        class ANormalClass:
            pass
        yield ANormalClass
        class AnotherNormalClass:
            pass
        yield AnotherNormalClass

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_class(self, cls):
        self.result = self.identifier.identify_class(cls)

    def it_should_ignore_it(self):
        assert self.result is None


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
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    @contexts.assertion
    def it_should_identify_it_as_examples(self):
        assert self.result is EXAMPLES


class WhenAnExamplesMethodIsAmbiguous:
    @classmethod
    def examples_of_ambiguous_examples_names(self):
        def method_with_example_and_establish_in_the_name():
            pass
        yield method_with_example_and_establish_in_the_name
        def method_with_example_and_because_in_the_name():
            pass
        yield method_with_example_and_because_in_the_name
        def method_with_example_and_should_in_the_name():
            pass
        yield method_with_example_and_should_in_the_name
        def method_with_example_and_cleanup_in_the_name():
            pass
        yield method_with_example_and_cleanup_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.exception = contexts.catch(self.identifier.identify_method, method)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenAnExamplesMethodIsNotSoAmbiguous:
    @classmethod
    def examples_of_not_so_ambiguous_examples_names(self):
        def method_with_example_and_data_in_the_name():
            pass
        yield method_with_example_and_data_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

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
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_identify_it_as_setup(self):
        assert self.result is SETUP


class WhenASetupMethodIsAmbiguous:
    @classmethod
    def examples_of_ambiguous_setup_names(self):
        def method_with_establish_and_examples_in_the_name():
            pass
        yield method_with_establish_and_examples_in_the_name
        def method_with_establish_and_because_in_the_name():
            pass
        yield method_with_establish_and_because_in_the_name
        def method_with_establish_and_should_in_the_name():
            pass
        yield method_with_establish_and_should_in_the_name
        def method_with_establish_and_cleanup_in_the_name():
            pass
        yield method_with_establish_and_cleanup_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.exception = contexts.catch(self.identifier.identify_method, method)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenASetupMethodIsNotSoAmbiguous:
    @classmethod
    def examples_of_not_so_ambiguous_setup_names(self):
        def method_with_establish_and_context_in_the_name():
            pass
        yield method_with_establish_and_context_in_the_name
        def method_with_context_and_given_in_the_name():
            pass
        yield method_with_context_and_given_in_the_name
        def method_with_given_and_establish_in_the_name():
            pass
        yield method_with_given_and_establish_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

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
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_identify_it_as_an_action(self):
        assert self.result is ACTION


class WhenAnActionMethodIsAmbiguous:
    @classmethod
    def examples_of_ambiguous_action_names(self):
        def method_with_because_and_examples_in_the_name():
            pass
        yield method_with_because_and_examples_in_the_name
        def method_with_because_and_establish_in_the_name():
            pass
        yield method_with_because_and_establish_in_the_name
        def method_with_because_and_should_in_the_name():
            pass
        yield method_with_because_and_should_in_the_name
        def method_with_because_and_cleanup_in_the_name():
            pass
        yield method_with_because_and_cleanup_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.exception = contexts.catch(self.identifier.identify_method, method)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenAnActionMethodIsNotSoAmbiguous:
    @classmethod
    def examples_of_not_so_ambiguous_action_names(self):
        def method_with_because_and_when_in_the_name():
            pass
        yield method_with_because_and_when_in_the_name
        def method_with_when_and_since_in_the_name(self):
            pass
        yield method_with_when_and_since_in_the_name
        def method_with_since_and_after_in_the_name(self):
            pass
        yield method_with_since_and_after_in_the_name
        def method_with_after_and_because_in_the_name(self):
            pass
        yield method_with_after_and_because_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

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
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_identify_it_as_an_assertion(self):
        assert self.result is ASSERTION


class WhenAnAssertionMethodIsAmbiguous:
    @classmethod
    def examples_of_ambiguous_assertion_names(self):
        def method_with_should_and_examples_in_the_name():
            pass
        yield method_with_should_and_examples_in_the_name
        def method_with_should_and_establish_in_the_name():
            pass
        yield method_with_should_and_establish_in_the_name
        def method_with_should_and_because_in_the_name():
            pass
        yield method_with_should_and_because_in_the_name
        def method_with_should_and_cleanup_in_the_name():
            pass
        yield method_with_should_and_cleanup_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.exception = contexts.catch(self.identifier.identify_method, method)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenAnAssertionMethodIsNotSoAmbiguous:
    @classmethod
    def examples_of_not_so_ambiguous_assertion_names(self):
        def method_with_it_and_should_in_the_name():
            pass
        yield method_with_it_and_should_in_the_name
        def method_with_should_and_then_in_the_name(self):
            pass
        yield method_with_should_and_then_in_the_name
        def method_with_then_and_must_in_the_name(self):
            pass
        yield method_with_then_and_must_in_the_name
        def method_with_must_and_will_in_the_name(self):
            pass
        yield method_with_must_and_will_in_the_name
        def method_with_will_and_it_in_the_name(self):
            pass
        yield method_with_will_and_it_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_identify_it_as_an_assertion(self):
        assert self.result is ASSERTION


class WhenIdentifyingATeardownMethod:
    @classmethod
    def examples_of_legal_teardown_names(self):
        def method_with_cleanup_in_the_name():
            pass
        yield method_with_cleanup_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_identify_it_as_a_teardown(self):
        assert self.result is TEARDOWN


class WhenATeardownMethodIsAmbiguous:
    @classmethod
    def examples_of_ambiguous_assertion_names(self):
        def method_with_cleanup_and_examples_in_the_name():
            pass
        yield method_with_cleanup_and_examples_in_the_name
        def method_with_cleanup_and_establish_in_the_name():
            pass
        yield method_with_cleanup_and_establish_in_the_name
        def method_with_cleanup_and_because_in_the_name():
            pass
        yield method_with_cleanup_and_because_in_the_name
        def method_with_cleanup_and_should_in_the_name():
            pass
        yield method_with_cleanup_and_should_in_the_name

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.exception = contexts.catch(self.identifier.identify_method, method)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenIdentiyingANormalMethod:
    @classmethod
    def examples_of_uninteresting_names(self):
        def an_innocuous_function(self):
            pass
        yield an_innocuous_function
        def another_method(self):
            pass
        yield another_method

    def establish(self):
        self.identifier = NameBasedIdentifier()

    def because_the_framework_asks_the_plugin_to_identify_the_method(self, method):
        self.result = self.identifier.identify_method(method)

    def it_should_ignore_it(self):
        assert self.result is None
