class Configuration(object):
    def __init__(self, shuffle):
        self.shuffle = shuffle

    def __eq__(self, other):
        return self.shuffle == other.shuffle
