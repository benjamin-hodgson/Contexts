import random


class Configuration(object):
    def __init__(self, shuffle, rewriting):
        self.shuffle = shuffle
        self.rewriting = rewriting

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
        return (self.shuffle == other.shuffle
            and self.rewriting == other.rewriting)

class NullConfiguration(object):
    def __init__(self):
        self.rewriting = False
    def process_module_list(self, l):
        pass
    def process_class_list(self, l):
        pass
    def process_assertion_list(self, l):
        pass
    def shuffle_list(self, l):
        pass
