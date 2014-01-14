import os
import shutil
import sys
import types
import contexts
from contexts.plugins.importing import Importer


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data")


class WhenImportingAModule:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.code = "x = 5"

        self.module_name = "test_file"
        self.write_file()

        self.importer = Importer()

    def because_we_import_the_file(self):
        self.module = self.importer.import_module(TEST_DATA_DIR, self.module_name)

    def it_should_return_the_module(self):
        assert isinstance(self.module, types.ModuleType)

    def it_should_run_the_code_in_the_module(self):
        assert self.module.x == 5

    def it_should_set_the_module_name(self):
        assert self.module.__name__ == self.module_name

    def it_should_set_the_module_file(self):
        assert self.module.__file__ == self.filename

    def it_should_put_the_module_in_sys_dot_modules(self):
        assert sys.modules[self.module_name] is self.module

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)
        del sys.modules[self.module_name]

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)


class WhenAFileFailsToImport:
    def establish_that_there_is_a_broken_file_in_the_filesystem(self):
        self.code = "raise ZeroDivisionError('bogus error message')"

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


class WhenAFileHasAlreadyBeenImported:
    def establish_that_we_have_already_imported_the_module(self):
        self.code = "is_fake = False"
        self.module_name = "already_imported_file"
        self.write_file()
        self.create_fake_module()

        self.importer = Importer()

    def because_we_import_the_module(self):
        self.result = self.importer.import_module(TEST_DATA_DIR, self.module_name)

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.module_name].is_fake

    def it_should_return_none(self):
        assert self.result is None

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)
        del sys.modules[self.module_name]

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + '.py')
        with open(self.filename, 'w+') as f:
            f.write(self.code)

    def create_fake_module(self):
        class TestSpec:
            def it(self):
                global module_ran
                module_ran = True
        test = types.ModuleType(self.module_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = self.filename
        test.TestSpec = TestSpec
        sys.modules[self.module_name] = test


class WhenADifferentModuleWithTheSameNameHasAlreadyBeenImported:
    def establish_that_we_have_already_imported_the_module(self):
        self.code = "is_fake = False"
        self.module_name = "already_imported_file"
        self.write_file()
        self.create_fake_module()

        self.importer = Importer()

    def because_we_import_the_module(self):
        self.result = self.importer.import_module(TEST_DATA_DIR, self.module_name)

    def it_should_return_the_new_module(self):
        assert not self.result.is_fake

    def it_should_put_the_new_module_in_sys_dot_modules(self):
        assert sys.modules[self.module_name] is self.result

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)
        del sys.modules[self.module_name]

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + '.py')
        with open(self.filename, 'w+') as f:
            f.write(self.code)

    def create_fake_module(self):
        class TestSpec:
            def it(self):
                global module_ran
                module_ran = True
        test = types.ModuleType(self.module_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = "made/up/file.py"
        test.TestSpec = TestSpec
        sys.modules[self.module_name] = test
