import random


class Configuration(object):
    def __init__(self, shuffle):
        self.shuffle = shuffle

    def process_module_list(self, l):
        self.shuffle_list(l)

    def process_class_list(self, l):
        self.shuffle_list(l)

    def process_assertion_list(self, l):
        self.shuffle_list(l)

    def shuffle_list(self, l):
        if self.shuffle:
            random.shuffle(l)

    def __eq__(self, other):
        return self.shuffle == other.shuffle
