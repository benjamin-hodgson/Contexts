import argparse
from contexts.plugins.object_supplier import TestObjectSupplier
from contexts.plugins.decorators import action


class WhenUserSpecifiesSomethingToRunOnTheCommandLine:
    def establish(self):
        self.object_supplier = TestObjectSupplier()
        self.args = argparse.Namespace()
        self.args.path = "made/up/path"
        self.object_supplier.initialise(self.args, {})

    @action
    def because_the_framework_asks_what_it_should_run(self):
        self.result = self.object_supplier.get_object_to_run()

    def it_should_return_the_path_the_user_specified(self):
        assert self.result == self.args.path
