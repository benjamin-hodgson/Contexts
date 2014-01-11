import contexts
from contexts.configuration import Configuration


class WhenInstantiatingTheConfiguration:
    def establish_that_we_have_some_arguments(self):
        self.rewriting = object()
    def because_we_instantiate_the_configuration(self):
        self.config = Configuration(shuffle=None, rewriting=self.rewriting)
    def config_dot_rewriting_should_be_whatever_we_passed_in(self):
        assert self.config.rewriting is self.rewriting


class WhenTwoConfigurationsAreEqual:
    @classmethod
    def examples(cls):
        yield {'shuffle':False, 'rewriting':False}
        yield {'shuffle':True, 'rewriting':False}
        yield {'shuffle':False, 'rewriting':True}
        yield {'shuffle':True, 'rewriting':True}
    def because_we_have_two_equal_configs(self, kwargs):
        self.config1 = Configuration(**kwargs)
        self.config2 = Configuration(**kwargs)
    def they_should_compare_equal(self):
        assert self.config1 == self.config2


class WhenTwoConfigurationsAreNotEqual:
    @classmethod
    def examples(cls):
        yield {'shuffle': True, 'rewriting':False}, {'shuffle': False, 'rewriting': False}
        yield {'shuffle': False, 'rewriting':True}, {'shuffle': False, 'rewriting': False}
    def because_we_have_two_different_configurations(self, kwargs1, kwargs2):
        self.config1 = Configuration(**kwargs1)
        self.config2 = Configuration(**kwargs2)
    def they_should_not_compare_equal(self):
        assert self.config1 != self.config2


class ShuffleIsTrueSharedContext:
    def establish_that_shuffle_is_true(self):
        self.list = list(range(100))
        self.original_list = self.list.copy()
        self.config = Configuration(shuffle=True, rewriting=False)


class ShuffleIsFalseSharedContext:
    def establish_that_shuffle_is_false(self):
        self.list = list(range(100))
        self.original_list = self.list.copy()
        self.config = Configuration(shuffle=False, rewriting=False)


# should really assert that it *randomises* the list, not just changes the order
class WhenProcessingAModuleListAndShuffleIsTrue(ShuffleIsTrueSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_modules(self):
        self.config.process_module_list(self.list)

    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list

    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)


class WhenProcessingAModuleListAndShuffleIsFalse(ShuffleIsFalseSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_modules(self):
        self.config.process_module_list(self.list)

    def it_should_not_modify_the_list(self):
        assert self.list == self.original_list


class WhenProcessingAClassListAndShuffleIsTrue(ShuffleIsTrueSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_classes(self):
        self.config.process_class_list(self.list)

    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list

    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)


class WhenProcessingAClassListAndShuffleIsFalse(ShuffleIsFalseSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_classes(self):
        self.config.process_class_list(self.list)

    def it_should_not_modify_the_list(self):
        assert self.list == self.original_list


class WhenProcessingAnAssertionListAndShuffleIsTrue(ShuffleIsTrueSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_assertions(self):
        self.config.process_assertion_list(self.list)

    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list

    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)


class WhenProcessingAnAssertionListAndShuffleIsFalse(ShuffleIsFalseSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_assertions(self):
        self.config.process_assertion_list(self.list)

    def it_should_not_modify_the_list(self):
        assert self.list == self.original_list
