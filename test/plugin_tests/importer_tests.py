import os
import contexts
from contexts.plugins.importing import Importer


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data")


class WhenAFileFailsToImport:
    def establish_that_there_is_a_broken_file_in_the_filesystem(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True

raise ZeroDivisionError("bogus error message")
"""
        self.module_name = "broken_test_file"
        self.write_file()

        self.importer = Importer()

    def because_we_try_to_import_the_file(self):
        self.exception = contexts.catch(self.importer.import_module, TEST_DATA_DIR, self.module_name)

    def it_should_propagate_the_exception(self):
        assert isinstance(self.exception, ZeroDivisionError)
        assert self.exception.args == ("bogus error message",)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)
