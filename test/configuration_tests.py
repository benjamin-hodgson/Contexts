from contexts.configuration import Configuration


class WhenInstantiatingTheConfiguration:
    def establish_that_we_have_some_arguments(self):
        self.shuffle = object()
    def because_we_instantiate_the_configuration(self):
        self.config = Configuration(self.shuffle)

    def config_dot_shuffle_should_be_whatever_we_passed_in(self):
        assert self.config.shuffle is self.shuffle


class WhenTwoConfigurationsAreEqual:
    @classmethod
    def examples(cls):
        yield False
        yield True

    def because_we_have_two_equal_configurations(self, shuffle):
        self.config1 = Configuration(shuffle)
        self.config2 = Configuration(shuffle)

    def they_should_compare_equal(self):
        assert self.config1 == self.config2


class WhenTwoConfigurationsAreNotEqual:
    def because_we_have_two_different_configurations(self):
        self.config1 = Configuration(True)
        self.config2 = Configuration(False)

    def they_should_not_compare_equal(self):
        assert self.config1 != self.config2
