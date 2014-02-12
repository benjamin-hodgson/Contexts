import argparse
import os.path
import contexts
from contexts.plugins.path_supplier import PathSupplier
from contexts import action


class WhenUserSpecifiesARealFile:
    def establish(self):
        self.path_supplier = PathSupplier()
        self.args = argparse.Namespace()
        self.args.path = __file__
        self.path_supplier.initialise(self.args, {})

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.path_supplier.get_object_to_run()

    def it_should_return_the_path_the_user_specified(self):
        assert self.result == self.args.path


class WhenUserSpecifiesARealFolder:
    def establish(self):
        self.path_supplier = PathSupplier()
        self.args = argparse.Namespace()
        self.args.path = os.path.dirname(__file__)
        self.path_supplier.initialise(self.args, {})

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.path_supplier.get_object_to_run()

    def it_should_return_the_path_the_user_specified(self):
        assert self.result == self.args.path


class WhenUserSpecifiesSomethingThatIsNotAFolder:
    def establish(self):
        self.path_supplier = PathSupplier()
        self.args = argparse.Namespace()
        self.args.path = "made/up/path"

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.exception = contexts.catch(self.path_supplier.initialise, self.args, {})

    def it_should_throw_a_ValueError(self):
        assert isinstance(self.exception, ValueError)
