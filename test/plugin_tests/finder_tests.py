import contexts
from contexts.plugins.finders import NameBasedFinder


###########################################################
# tests for get_setup_methods
###########################################################

class WhenFindingSetupMethods:
    @classmethod
    def examples_of_valid_setup_names(cls):
        class Establish:
            def method_with_establish_in_the_name(self):
                pass
        yield Establish, Establish.method_with_establish_in_the_name

        class Context:
            def method_with_context_in_the_name(self):
                pass
        yield Context, Context.method_with_context_in_the_name

        class Given:
            def method_with_given_in_the_name(self):
                pass
        yield Given, Given.method_with_given_in_the_name

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self, spec, method):
        self.result = self.finder.get_setup_methods(spec)

    def it_should_return_the_setup_method(self, spec, method):
        assert self.result == [method]


class WhenASuperclassDefinesASetupMethod:
    @classmethod
    def examples_of_ways_superclasses_can_define_methods(self):
        class SuperGiven:
            def given(self):
                pass
        class SpecContext(SuperGiven):
            def context(self):
                pass
        yield SpecContext, SuperGiven.given, SpecContext.context

        # I want it to run the superclass's methods _even if_
        # they have the same name as the subclass method
        class SuperEstablish:
            def establish(self):
                pass
        class SpecEstablish(SuperEstablish):
            def establish(self):
                pass
        yield SpecEstablish, SuperEstablish.establish, SpecEstablish.establish

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self, spec, super_method, spec_method):
        self.result = self.finder.get_setup_methods(spec)

    @contexts.assertion
    def it_should_return_the_superclass_method_and_then_the_subclass_method(self, spec, super_method, spec_method):
        assert self.result == [super_method, spec_method]


class WhenMultipleSetupMethodsAreDefined:
    def establish_that_a_spec_has_multiple_setups(self):
        class MultipleSetups:
            def method_with_establish_in_the_name(self):
                pass
            def another_method_with_establish_in_the_name(self):
                pass
        self.spec = MultipleSetups
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self):
        self.exception = contexts.catch(self.finder.get_setup_methods, self.spec)

    def it_should_throw_a_TooManySpecialMethodsError(self):
        assert isinstance(self.exception, contexts.errors.TooManySpecialMethodsError)


class WhenASetupMethodIsAmbiguouslyNamed:
    @classmethod
    def examples_of_specs_with_ambiguous_setup_methods(cls):
        class AmbiguousSetup1:
            def method_with_establish_and_because_in_the_name(self):
                pass
        yield AmbiguousSetup1

        class AmbiguousSetup2:
            def method_with_establish_and_should_in_the_name(self):
                pass
        yield AmbiguousSetup2

        class AmbiguousSetup3:
            def method_with_establish_and_cleanup_in_the_name(self):
                pass
        yield AmbiguousSetup3

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self, spec):
        self.exception = contexts.catch(self.finder.get_setup_methods, spec)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenASetupMethodIsNotSoAmbiguouslyNamed:
    @classmethod
    def examples_of_specs_with_not_so_ambiguous_setup_methods(cls):
        class NotSoAmbiguousSetup1:
            def method_with_establish_and_given_in_the_name(self):
                pass
        yield NotSoAmbiguousSetup1, NotSoAmbiguousSetup1.method_with_establish_and_given_in_the_name

        class NotSoAmbiguousSetup2:
            def method_with_given_and_context_in_the_name(self):
                pass
        yield NotSoAmbiguousSetup2, NotSoAmbiguousSetup2.method_with_given_and_context_in_the_name

        class NotSoAmbiguousSetup3:
            def method_with_establish_and_context_in_the_name(self):
                pass
        yield NotSoAmbiguousSetup3, NotSoAmbiguousSetup3.method_with_establish_and_context_in_the_name

    def establish(self, spec, _):
        self.spec = spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self):
        self.result = self.finder.get_setup_methods(self.spec)

    def it_should_return_the_setup_method(self, _, method):
        assert self.result == [method]


class WhenANonFunctionObjectHasASetupName:
    def establish_that_a_spec_has_establish_not_bound_to_a_function(self):
        class Spec:
            establish = 123
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_setup_methods(self):
        self.result = self.finder.get_setup_methods(self.spec)

    def it_should_not_return_the_non_function(self):
        assert self.result == []


###########################################################
# tests for get_action_method
###########################################################

class WhenFindingAnActionMethod:
    @classmethod
    def examples_of_valid_action_names(cls):
        class Because:
            def method_with_because_in_the_name(self):
                pass
        yield Because, Because.method_with_because_in_the_name

        class When:
            def method_with_when_in_the_name(self):
                pass
        yield When, When.method_with_when_in_the_name

        class Since:
            def method_with_since_in_the_name(self):
                pass
        yield Since, Since.method_with_since_in_the_name

        class After:
            def method_with_after_in_the_name(self):
                pass
        yield After, After.method_with_after_in_the_name

    def establish(self, spec, _):
        self.spec = spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self):
        self.result = self.finder.get_action_method(self.spec)

    def it_should_return_the_action_method(self, _, method):
        assert self.result == method


class WhenASuperclassDefinesAnActionMethod:
    def establish_that_a_spec_has_a_superclass(self):
        class Super:
            def because(self):
                pass
        class Spec(Super):
            pass
        self.super = Super
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self):
        self.result = self.finder.get_action_method(self.spec)

    def it_should_not_return_the_superclass_action_method(self):
        assert self.result is None


class WhenMultipleActionMethodsAreDefined:
    def establish_that_the_class_has_multiple_actions(self):
        class MultipleActions:
            def method_with_because_in_the_name(self):
                pass
            def another_method_with_because_in_the_name(self):
                pass
        self.spec = MultipleActions
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self):
        self.exception = contexts.catch(self.finder.get_action_method, self.spec)

    def it_should_throw_a_TooManySpecialMethodsError(self):
        assert isinstance(self.exception, contexts.errors.TooManySpecialMethodsError)


class WhenAnActionMethodIsAmbiguouslyNamed:
    @classmethod
    def examples_of_specs_with_ambiguous_action_methods(cls):
        class AmbiguousAction1:
            def method_with_because_and_establish_in_the_name(self):
                pass
        yield AmbiguousAction1

        class AmbiguousAction2:
            def method_with_because_and_should_in_the_name(self):
                pass
        yield AmbiguousAction2

        class AmbiguousAction3:
            def method_with_because_and_cleanup_in_the_name(self):
                pass
        yield AmbiguousAction3

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self, spec):
        self.exception = contexts.catch(self.finder.get_action_method, spec)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenAnActionMethodIsNotSoAmbiguouslyNamed:
    @classmethod
    def examples_of_specs_with_not_so_ambiguous_setup_methods(cls):
        class NotSoAmbiguousAction1:
            def method_with_because_and_when_in_the_name(self):
                pass
        yield NotSoAmbiguousAction1, NotSoAmbiguousAction1.method_with_because_and_when_in_the_name

        class NotSoAmbiguousAction2:
            def method_with_when_and_after_in_the_name(self):
                pass
        yield NotSoAmbiguousAction2, NotSoAmbiguousAction2.method_with_when_and_after_in_the_name

        class NotSoAmbiguousAction3:
            def method_with_after_and_since_in_the_name(self):
                pass
        yield NotSoAmbiguousAction3, NotSoAmbiguousAction3.method_with_after_and_since_in_the_name

        class NotSoAmbiguousAction3:
            def method_with_since_and_because_in_the_name(self):
                pass
        yield NotSoAmbiguousAction3, NotSoAmbiguousAction3.method_with_since_and_because_in_the_name

    def establish(self, spec, _):
        self.spec = spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self):
        self.result = self.finder.get_action_method(self.spec)

    def it_should_return_the_setup_method(self, _, method):
        assert self.result == method


class WhenANonFunctionObjectHasAnActionName:
    @contexts.setup
    def establish_that_a_spec_has_because_not_bound_to_a_function(self):
        class Spec:
            because = 123
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_action_method(self):
        self.result = self.finder.get_action_method(self.spec)

    def it_should_not_return_the_non_function(self):
        assert self.result is None

