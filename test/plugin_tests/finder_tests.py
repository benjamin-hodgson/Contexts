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


###########################################################
# tests for get_assertion_methods
###########################################################

class WhenFindingAssertionMethods:
    def given_a_class_with_assertion_methods(self):
        class AssertionMethods:
            def method_with_it_in_the_name(self):
                pass
            def method_with_should_in_the_name(self):
                pass
            def method_with_must_in_the_name(self):
                pass
            def method_with_will_in_the_name(self):
                pass
            def method_with_then_in_the_name(self):
                pass
        self.spec = AssertionMethods
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_assertion_methods(self):
        self.result = self.finder.get_assertion_methods(self.spec)

    def it_should_return_all_the_assertion_methods(self):
        assert set(self.result) == {
            self.spec.method_with_it_in_the_name,
            self.spec.method_with_must_in_the_name,
            self.spec.method_with_should_in_the_name,
            self.spec.method_with_then_in_the_name,
            self.spec.method_with_will_in_the_name
        }


class WhenASuperclassDefinesAssertionMethods:
    def given_a_superclass_with_assertions(self):
        class Super:
            def should(self):
                pass
        class Spec(Super):
            pass
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_assertion_methods(self):
        self.result = self.finder.get_assertion_methods(self.spec)

    def it_should_not_return_the_superclass_methods(self):
        assert self.result == []


class WhenAnAssertionMethodIsAmbiguouslyNamed:
    @classmethod
    def examples_of_ambiguous_assertion_methods(cls):
        class AmbiguousAssertion1:
            def method_with_should_and_establish_in_the_name(self):
                pass
        yield AmbiguousAssertion1

        class AmbiguousAssertion2:
            def method_with_should_and_because_in_the_name(self):
                pass
        yield AmbiguousAssertion2

        class AmbiguousAssertion3:
            def method_with_should_and_cleanup_in_the_name(self):
                pass
        yield AmbiguousAssertion3

    def context(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_assertion_methods(self, spec):
        self.exception = contexts.catch(self.finder.get_assertion_methods, spec)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenAnAssertionMethodIsNotSoAmbiguouslyNamed:
    @classmethod
    def examples_of_not_so_ambiguous_assertion_methods(cls):
        class NotSoAmbiguousAssertion1:
            def method_with_it_and_should_in_the_name(self):
                pass
        yield NotSoAmbiguousAssertion1, NotSoAmbiguousAssertion1.method_with_it_and_should_in_the_name

        class NotSoAmbiguousAssertion2:
            def method_with_should_and_must_in_the_name(self):
                pass
        yield NotSoAmbiguousAssertion2, NotSoAmbiguousAssertion2.method_with_should_and_must_in_the_name

        class NotSoAmbiguousAssertion3:
            def method_with_must_and_will_in_the_name(self):
                pass
        yield NotSoAmbiguousAssertion3, NotSoAmbiguousAssertion3.method_with_must_and_will_in_the_name

        class NotSoAmbiguousAssertion4:
            def method_with_will_and_then_in_the_name(self):
                pass
        yield NotSoAmbiguousAssertion4, NotSoAmbiguousAssertion4.method_with_will_and_then_in_the_name

        class NotSoAmbiguousAssertion5:
            def method_with_then_and_it_in_the_name(self):
                pass
        yield NotSoAmbiguousAssertion5, NotSoAmbiguousAssertion5.method_with_then_and_it_in_the_name

    def context(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_assertion_methods(self, spec, method):
        self.result = self.finder.get_assertion_methods(spec)

    def it_should_return_the_method(self, spec, method):
        assert self.result == [method]


class WhenANonFunctionObjectHasAnAssertionName:
    @contexts.setup
    def establish_that_a_spec_has_should_not_bound_to_a_function(self):
        class Spec:
            should = 123
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_assertion_methods(self):
        self.result = self.finder.get_assertion_methods(self.spec)

    def it_should_not_return_the_non_function(self):
        assert self.result == []


###########################################################
# tests for get_teardown_methods
###########################################################

class WhenFindingTeardownMethods:
    def establish(self):
        class Cleanup:
            def method_with_cleanup_in_the_name(self):
                pass
        self.spec = Cleanup
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_teardown_methods(self):
        self.result = self.finder.get_teardown_methods(self.spec)

    def it_should_return_the_setup_method(self):
        assert self.result == [self.spec.method_with_cleanup_in_the_name]


class WhenASuperclassDefinesATeardownMethod:
    @classmethod
    def examples_of_ways_superclasses_can_define_methods(self):
        class Super:
            def superclass_cleanup_method(self):
                pass
        class Spec(Super):
            def subclass_cleanup_method(self):
                pass
        yield Spec, Super.superclass_cleanup_method, Spec.subclass_cleanup_method

        # I want it to run the superclass's methods _even if_
        # they have the same name as the subclass method
        class Super:
            def cleanup(self):
                pass
        class Spec(Super):
            def cleanup(self):
                pass
        yield Spec, Super.cleanup, Spec.cleanup

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_teardown_methods(self, spec, super_method, spec_method):
        self.result = self.finder.get_teardown_methods(spec)

    @contexts.assertion
    def it_should_return_the_subclass_method_and_then_the_superclass_method(self, spec, super_method, spec_method):
        assert self.result == [spec_method, super_method]


class WhenMultipleTeardownMethodsAreDefined:
    def establish_that_a_spec_has_multiple_teardowns(self):
        class MultipleTeardowns:
            def method_with_cleanup_in_the_name(self):
                pass
            def another_method_with_cleanup_in_the_name(self):
                pass
        self.spec = MultipleTeardowns
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_teardown_methods(self):
        self.exception = contexts.catch(self.finder.get_teardown_methods, self.spec)

    def it_should_throw_a_TooManySpecialMethodsError(self):
        assert isinstance(self.exception, contexts.errors.TooManySpecialMethodsError)


class WhenATeardownMethodIsAmbiguouslyNamed:
    @classmethod
    def examples_of_specs_with_ambiguous_teardown_methods(cls):
        class AmbiguousTeardown1:
            def method_with_cleanup_and_establish_in_the_name(self):
                pass
        yield AmbiguousTeardown1

        class AmbiguousTeardown2:
            def method_with_cleanup_and_because_in_the_name(self):
                pass
        yield AmbiguousTeardown2

        class AmbiguousTeardown3:
            def method_with_cleanup_and_should_in_the_name(self):
                pass
        yield AmbiguousTeardown3

    def establish(self):
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_teardown_methods(self, spec):
        self.exception = contexts.catch(self.finder.get_teardown_methods, spec)

    def it_should_throw_a_MethodNamingError(self):
        assert isinstance(self.exception, contexts.errors.MethodNamingError)


class WhenANonFunctionObjectHasATeardownName:
    @contexts.setup
    def establish_that_a_spec_has_cleanup_not_bound_to_a_function(self):
        class Spec:
            cleanup = 123
        self.spec = Spec
        self.finder = NameBasedFinder()

    def when_the_framework_calls_get_teardown_methods(self):
        self.result = self.finder.get_teardown_methods(self.spec)

    def it_should_not_return_the_non_function(self):
        assert self.result == []
