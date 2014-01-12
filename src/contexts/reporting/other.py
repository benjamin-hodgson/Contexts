import random


class Shuffler(object):
    def process_module_list(self, l):
        self.shuffle_list(l)
    def process_class_list(self, l):
        self.shuffle_list(l)
    def process_assertion_list(self, l):
        self.shuffle_list(l)
    def shuffle_list(self, l):
        random.shuffle(l)

    def __eq__(self, other):
        return isinstance(other, Shuffler)
