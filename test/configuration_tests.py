from unittest import mock
import contexts
from contexts.configuration import Configuration, Shuffler


class WhenInstantiatingTheConfiguration:
    def establish_that_we_have_some_arguments(self):
        self.plugins = [mock.Mock(), mock.Mock()]
        self.rewriting = mock.Mock()

    def because_we_instantiate_the_configuration(self):
        self.config = Configuration(rewriting=self.rewriting, plugins=self.plugins)

    def config_dot_rewriting_should_be_whatever_we_passed_in(self):
        assert self.config.rewriting is self.rewriting

    def it_should_put_the_plugins_in_its_list(self):
        assert self.config.plugins == self.plugins


class WhenTwoConfigurationsAreEqual:
    @classmethod
    def examples(cls):
        yield {'rewriting':False}
        yield {'rewriting':False}
        yield {'rewriting':True}
        yield {'rewriting':True}
        yield {'plugins': (mock.Mock(),)}
        yield {'plugins': ('a', 1)}
        yield {'plugins': (12.3, [], None)}
    def because_we_have_two_equal_configs(self, kwargs):
        self.config1 = Configuration(**kwargs)
        self.config2 = Configuration(**kwargs)
    def they_should_compare_equal(self):
        assert self.config1 == self.config2


class WhenTwoConfigurationsAreNotEqual:
    @classmethod
    def examples(cls):
        yield {'rewriting':True}, {'rewriting': False}
        yield {'plugins': (mock.Mock(),)}, {'plugins': (mock.Mock(),)}
        yield {'plugins': ('a',)}, {'plugins': ()}
    def because_we_have_two_different_configurations(self, kwargs1, kwargs2):
        self.config1 = Configuration(**kwargs1)
        self.config2 = Configuration(**kwargs2)
    def they_should_not_compare_equal(self):
        assert self.config1 != self.config2


class WhenCallingPluginMethods:
    @classmethod
    def examples_of_method_names(cls):
        yield "plugin_method"
        yield "another_plugin_method"
        yield "third_plugin_method"

    def establish_that_the_config_contains_plugins(self):
        self.plugin_master = mock.Mock()
        plugins = [self.plugin_master.plugin1,
                   self.plugin_master.plugin2,
                   self.plugin_master.plugin3]

        self.config = Configuration(plugins=plugins)

    def because_we_call_a_plugin_method(self, method_name):
        getattr(self.config, method_name)(1, [3], x=None)

    def it_should_delegate_to_the_plugins_in_the_correct_order(self, method_name):
        assert self.plugin_master.mock_calls == [getattr(mock.call.plugin1, method_name)(1, [3], x=None),
                                                 getattr(mock.call.plugin2, method_name)(1, [3], x=None),
                                                 getattr(mock.call.plugin3, method_name)(1, [3], x=None)]


###########################################################
# tests for Shuffler
###########################################################

class ShufflerSharedContext:
    def establish_that_shuffle_is_true(self):
        self.list = list(range(100))
        self.original_list = self.list.copy()
        self.shuffler = Shuffler()

# should really assert that it *randomises* the list, not just changes the order
class WhenProcessingAModuleListAndShuffleIsTrue(ShufflerSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_modules(self):
        self.shuffler.process_module_list(self.list)
    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list
    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)

class WhenProcessingAClassListAndShuffleIsTrue(ShufflerSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_classes(self):
        self.shuffler.process_class_list(self.list)
    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list
    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)

class WhenProcessingAnAssertionListAndShuffleIsTrue(ShufflerSharedContext):
    @contexts.action
    def because_we_ask_it_to_process_the_list_of_assertions(self):
        self.shuffler.process_assertion_list(self.list)

    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list

    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)
