from contexts.plugins.shuffling import Shuffler
from contexts import action

class ShufflerSharedContext:
    def establish_that_shuffle_is_true(self):
        self.list = list(range(100))
        self.original_list = self.list.copy()
        self.shuffler = Shuffler()

# should really assert that it *randomises* the list, not just changes the order
class WhenProcessingAModuleListAndShuffleIsTrue(ShufflerSharedContext):
    @action
    def because_we_ask_it_to_process_the_list_of_modules(self):
        self.shuffler.process_module_list(self.list)
    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list
    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)

class WhenProcessingAClassListAndShuffleIsTrue(ShufflerSharedContext):
    @action
    def because_we_ask_it_to_process_the_list_of_classes(self):
        self.shuffler.process_class_list(None, self.list)
    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list
    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)

class WhenProcessingAnAssertionListAndShuffleIsTrue(ShufflerSharedContext):
    @action
    def because_we_ask_it_to_process_the_list_of_assertions(self):
        self.shuffler.process_assertion_list(None, self.list)
    def it_should_shuffle_the_list_in_place(self):
        assert self.list != self.original_list
    def it_should_not_change_the_contents_of_the_list(self):
        assert set(self.list) == set(self.original_list)
