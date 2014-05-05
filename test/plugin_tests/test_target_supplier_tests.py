import argparse
import os.path
import contexts
from contexts.plugins.test_target_suppliers import CommandLineSupplier, ObjectSupplier
from contexts import action


class WhenUserSpecifiesARealFile:
    def establish(self):
        self.supplier = CommandLineSupplier()
        self.args = argparse.Namespace()
        self.args.path = __file__
        self.supplier.initialise(self.args, {})

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.supplier.get_object_to_run()

    def it_should_return_the_path_the_user_specified(self):
        assert self.result == self.args.path


class WhenUserSpecifiesARealFolder:
    def establish(self):
        self.supplier = CommandLineSupplier()
        self.args = argparse.Namespace()
        self.args.path = os.path.dirname(__file__)
        self.supplier.initialise(self.args, {})

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.supplier.get_object_to_run()

    def it_should_return_the_path_the_user_specified(self):
        assert self.result == self.args.path


class WhenUserSpecifiesAClassInAPythonModule:
    def establish(self):
        self.supplier = CommandLineSupplier()
        self.args = argparse.Namespace()
        self.args.path = __file__ + ":WhenUserSpecifiesARealFile"


class WhenUserSpecifiesSomethingThatIsNotAFolder:
    def establish(self):
        self.supplier = CommandLineSupplier()
        self.args = argparse.Namespace()
        self.args.path = "made/up/path"

    def because_we_try_to_initialise_the_plugin(self):
        self.exception = contexts.catch(self.supplier.initialise, self.args, {})

    def it_should_throw_a_ValueError(self):
        assert isinstance(self.exception, ValueError)


class WhenClientSpecifiesAnObject:
    def establish_that_something_has_been_injected(self):
        self.target = object()
        self.object_supplier = ObjectSupplier(self.target)

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.object_supplier.get_object_to_run()

    def it_should_return_what_was_injected(self):
        assert self.result is self.target
