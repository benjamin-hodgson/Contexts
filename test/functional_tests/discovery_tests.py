import importlib
import os
import shutil
import sys
import types
import contexts
from .tools import SpyReporter


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data")


class WhenRunningAModule:
    def context(self):
        class HasSpecInTheName:
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class HasWhenInTheName:
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class NormalClass:
            was_instantiated = False
            def __init__(self):
                self.__class__.was_instantiated = True
        self.module = types.ModuleType('fake_specs')
        self.module.HasSpecInTheName = HasSpecInTheName
        self.module.HasWhenInTheName = HasWhenInTheName
        self.module.NormalClass = NormalClass

        self.reporter = SpyReporter()

    def because_we_run_the_module(self):
        contexts.run(self.module, [self.reporter])

    def it_should_run_the_spec(self):
        assert self.module.HasSpecInTheName.was_run

    def it_should_run_the_other_spec(self):
        assert self.module.HasWhenInTheName.was_run

    def it_should_not_instantiate_the_normal_class(self):
        assert not self.module.NormalClass.was_instantiated

    def it_should_call_suite_started(self):
        assert self.reporter.calls[1][0] == "suite_started"

    def it_should_pass_the_suite_object_into_suite_started(self):
        assert self.reporter.calls[1][1].name == self.module.__name__

    def it_should_call_suite_ended(self):
        assert self.reporter.calls[-2][0] == "suite_ended"

    def it_should_pass_the_suite_object_into_suite_ended(self):
        assert self.reporter.calls[-2][1].name == self.module.__name__


class WhenRunningTheSameModuleMultipleTimes:
    # too hard to test that shuffling works for a whole filesystem of tests :(
    def context(self):
        self.create_module()

        self.reporter1 = SpyReporter()
        self.reporter2 = SpyReporter()

    def because_we_run_the_module_twice(self):
        contexts.run(self.module, [self.reporter1])
        contexts.run(self.module, [self.reporter2])

    @contexts.assertion
    def it_should_run_the_contexts_in_a_different_order(self):
        first_order = [call[1].name for call in self.reporter1.calls if call[0] == "context_started"]
        second_order = [call[1].name for call in self.reporter2.calls if call[0] == "context_started"]
        assert first_order != second_order

    def create_module(self):
        self.module = types.ModuleType("specs")

        for x in range(100):
            class_name = "Spec" + str(x)
            def it(self):
                pass
            cls = type(class_name, (object,), {'it': it})
            setattr(self.module, class_name, cls)


class WhenRunningAFile:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.module_name = "test_file"
        self.write_file()
        self.reporter = SpyReporter()

    def because_we_run_the_file(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_import_the_file(self):
        assert self.module_name in sys.modules

    def it_should_run_the_specs(self):
        assert sys.modules[self.module_name].module_ran

    def it_should_call_suite_started(self):
        assert self.reporter.calls[1][0] == "suite_started"

    def it_should_pass_the_suite_object_into_suite_started(self):
        assert self.reporter.calls[1][1].name == self.module_name

    def it_should_call_suite_ended(self):
        assert self.reporter.calls[-2][0] == "suite_ended"

    def it_should_pass_the_suite_object_into_suite_ended(self):
        assert self.reporter.calls[-2][1].name == self.module_name

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)
        del sys.modules[self.module_name]
        importlib.invalidate_caches()

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)


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
        self.reporter = SpyReporter()

    def because_we_run_the_file(self):
        contexts.run(self.filename, [self.reporter])

    def it_should_call_unexpected_error_on_the_reporter(self):
        assert self.reporter.calls[1][0] == "unexpected_error"

    def it_should_pass_in_the_exception(self):
        assert isinstance(self.reporter.calls[1][1], ZeroDivisionError)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        os.remove(self.filename)
        importlib.invalidate_caches()

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)


class WhenRunningAFolderWhichIsNotAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.module_names = ["test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

        self.reporter = SpyReporter()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.reporter])

    def it_should_import_the_first_module(self):
        assert self.module_names[0] in sys.modules

    def it_should_import_the_second_module(self):
        assert self.module_names[1] in sys.modules

    def it_should_run_the_first_module(self):
        assert sys.modules[self.module_names[0]].module_ran

    def it_should_run_the_second_module(self):
        assert sys.modules[self.module_names[1]].module_ran

    def it_should_not_run_the_non_test_module(self):
        assert self.module_names[2] not in sys.modules

    def it_should_call_suite_started_for_both_modules(self):
        assert self.reporter.calls[1][0] == 'suite_started'
        assert self.reporter.calls[7][0] == 'suite_started'

    def it_should_pass_the_suites_into_suite_started(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'test_file1', 'test_file2'}

    def it_should_call_suite_ended_for_both_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'

    def it_should_pass_the_suites_into_suite_ended(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'test_file1', 'test_file2'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_names[0]]
        del sys.modules[self.module_names[1]]
        importlib.invalidate_caches()

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n+".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)


class WhenAFolderContainsAnAlreadyImportedFile:
    def establish_that_we_have_already_imported_the_module(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.module_name = "test1"
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [])

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.module_name].is_fake

    def it_should_not_re_run_the_module(self):
        assert not sys.modules[self.module_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_name]
        importlib.invalidate_caches()

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

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder2')
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filename = os.path.join(self.folder_path, self.module_name + '.py')
        with open(self.filename, 'w+') as f:
            f.write(self.code)


class WhenAFolderContainsAFileWithTheSameNameAsAnAlreadyImportedModule:
    def establish_that_we_have_imported_a_module_with_the_same_name(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.module_name = "test2"
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [])

    def it_should_import_the_new_module_and_overwrite_the_old_one(self):
        assert not sys.modules[self.module_name].is_fake

    def it_should_run_the_first_module(self):
        assert sys.modules[self.module_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_name]
        importlib.invalidate_caches()

    def create_fake_module(self):
        test = types.ModuleType(self.module_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = os.path.join("fake", "file.py")
        sys.modules[self.module_name] = test

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder2')
        os.mkdir(self.folder_path)

    def write_files(self):
        filename = os.path.join(self.folder_path, self.module_name + '.py')
        with open(filename, 'w+') as f:
            f.write(self.code)


class WhenAPackageHasAlreadyBeenImported:
    def establish_that_we_have_already_imported_the_package(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.package_name = 'already_imported_package'
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_package(self):
        contexts.run(self.folder_path, [])

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.package_name].is_fake

    def it_should_not_re_run_the_module(self):
        assert not sys.modules[self.package_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name]
        importlib.invalidate_caches()

    def create_fake_module(self):
        class TestSpec:
            def it(self):
                global module_ran
                module_ran = True
        test = types.ModuleType(self.package_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = self.filename
        test.TestSpec = TestSpec
        sys.modules[self.package_name] = test

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filename = os.path.join(self.folder_path, '__init__.py')
        with open(self.filename, 'w') as f:
            f.write(self.code)


class WhenAPackageHasTheSameNameAsAnAlreadyImportedModule:
    def establish_that_we_have_imported_a_module_with_the_same_name(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.package_name = 'package_folder_coincidence'
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [])

    def it_should_import_the_new_module_and_overwrite_the_old_one(self):
        assert not sys.modules[self.package_name].is_fake

    def it_should_run_the_first_module(self):
        assert sys.modules[self.package_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name]
        importlib.invalidate_caches()

    def create_fake_module(self):
        test = types.ModuleType(self.package_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = os.path.join("fake", "file.py")
        sys.modules[self.package_name] = test

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filename = os.path.join(self.folder_path, '__init__.py')
        with open(self.filename, 'w') as f:
            f.write(self.code)


class WhenAPackageContainsAnAlreadyImportedFile:
    def establish_that_we_have_already_imported_the_module(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.package_name = 'package_folder_with_already_imported_file'
        self.module_name = "already_imported_test"
        self.qualified_name = self.package_name + '.' + self.module_name
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_package(self):
        contexts.run(self.folder_path, [])

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.qualified_name].is_fake

    def it_should_not_re_run_the_module(self):
        assert not sys.modules[self.qualified_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.qualified_name]
        importlib.invalidate_caches()

    def create_fake_module(self):
        class TestSpec:
            def it(self):
                global module_ran
                module_ran = True
        test = types.ModuleType(self.qualified_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = self.filename
        test.TestSpec = TestSpec
        sys.modules[self.qualified_name] = test

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filename = os.path.join(self.folder_path, self.module_name + '.py')
        with open(os.path.join(self.folder_path, '__init__.py'), 'w') as f:
            f.write('')
        with open(self.filename, 'w+') as f:
            f.write(self.code)


class WhenAPackageContainsAFileWithTheSameNameAsAnAlreadyImportedModule:
    def establish_that_we_have_imported_a_module_with_the_same_name(self):
        self.code = """
module_ran = False
is_fake = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.package_name = 'package_folder_with_matching_filename'
        self.module_name = "maybe_imported_test"
        self.qualified_name = self.package_name + '.' + self.module_name
        self.create_folder()
        self.write_files()
        self.create_fake_module()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [])

    def it_should_import_the_new_module_and_overwrite_the_old_one(self):
        assert not sys.modules[self.qualified_name].is_fake

    def it_should_run_the_first_module(self):
        assert sys.modules[self.qualified_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.qualified_name]
        importlib.invalidate_caches()

    def create_fake_module(self):
        test = types.ModuleType(self.qualified_name)
        test.is_fake = True
        test.module_ran = False
        test.__file__ = os.path.join("fake", "file.py")
        sys.modules[self.qualified_name] = test

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        filename = os.path.join(self.folder_path, self.module_name + '.py')
        with open(os.path.join(self.folder_path, '__init__.py'), 'w') as f:
            f.write('')
        with open(filename, 'w+') as f:
            f.write(self.code)


class WhenRunningAFolderWhichIsAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.package_name = 'package_folder'
        self.module_names = ["__init__", "test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

        self.reporter = SpyReporter()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.reporter])

    def it_should_import_the_package(self):
        assert self.package_name in sys.modules

    def it_should_import_the_first_module(self):
        assert self.package_name + '.' + self.module_names[1] in sys.modules

    def it_should_only_import_the_first_module_using_its_full_name(self):
        assert self.module_names[1] not in sys.modules

    def it_should_import_the_second_module(self):
        assert self.package_name + '.' + self.module_names[2] in sys.modules

    def it_should_only_import_the_second_module_using_its_full_name(self):
        assert self.module_names[1] not in sys.modules

    def it_should_not_import_the_third_module(self):
        assert self.package_name + '.' + self.module_names[3] not in sys.modules
        assert self.module_names[3] not in sys.modules

    def it_should_not_import_something_called_init(self):
        assert "__init__" not in sys.modules
        assert "package_folder.__init__" not in sys.modules

    def it_should_run_the_package(self):
        assert sys.modules[self.package_name].module_ran

    def it_should_run_the_first_module(self):
        assert sys.modules[self.package_name + '.' + self.module_names[1]].module_ran

    def it_should_run_the_second_module(self):
        assert sys.modules[self.package_name + '.' + self.module_names[2]].module_ran

    def it_should_call_suite_started_for_three_modules(self):
        assert self.reporter.calls[1][0] == 'suite_started'
        assert self.reporter.calls[7][0] == 'suite_started'
        assert self.reporter.calls[13][0] == 'suite_started'

    def it_should_pass_the_suites_into_suite_started(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'package_folder', 'package_folder.test_file1', 'package_folder.test_file2'}

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'

    def it_should_pass_the_suites_into_suite_ended(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'package_folder', 'package_folder.test_file1', 'package_folder.test_file2'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name + '.' + self.module_names[1]]
        del sys.modules[self.package_name + '.' + self.module_names[2]]
        del sys.modules[self.package_name]
        importlib.invalidate_caches()

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n + ".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)


class WhenRunningAFolderWithSubfolders:
    def establish_that_there_is_a_folder_containing_subfolders(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.folder_name = 'folder3'
        self.tree = {
            "test_subfolder": ["test_file1"],
            "test_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

        self.reporter = SpyReporter()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.reporter])

    def it_should_import_the_file_in_the_test_folder(self):
        assert "test_file1" in sys.modules

    def it_should_run_the_file_in_the_test_folder(self):
        assert sys.modules["test_file1"].module_ran

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        assert "test_file3" not in sys.modules

    def it_should_import_the_test_package(self):
        assert "test_subpackage" in sys.modules

    def it_should_run_the_test_package(self):
        assert sys.modules["test_subpackage"].module_ran

    def it_should_import_the_file_in_the_test_package(self):
        assert "test_subpackage.test_file2" in sys.modules

    def it_should_only_import_the_file_in_the_test_package_using_its_full_name(self):
        assert "test_file2" not in sys.modules

    def it_should_run_the_file_in_the_test_package(self):
        assert sys.modules["test_subpackage.test_file2"].module_ran

    def it_should_not_import_the_non_test_package(self):
        assert "another_subpackage" not in sys.modules

    def it_should_not_import_the_file_in_the_non_test_package(self):
        assert "another_subpackage.test_file4" not in sys.modules
        assert "test_file4" not in sys.modules

    def it_should_not_import_anything_called_init(self):
        assert "__init__" not in sys.modules
        assert "test_subpackage.__init__" not in sys.modules
        assert "another_subpackage.__init__" not in sys.modules

    def it_should_call_suite_started_for_three_modules(self):
        assert self.reporter.calls[1][0] == 'suite_started'
        assert self.reporter.calls[7][0] == 'suite_started'
        assert self.reporter.calls[13][0] == 'suite_started'

    def it_should_pass_the_suites_into_suite_started(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'test_file1', 'test_subpackage', 'test_subpackage.test_file2'}

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'

    def it_should_pass_the_suites_into_suite_ended(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'test_file1', 'test_subpackage', 'test_subpackage.test_file2'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["test_subpackage"]
        del sys.modules["test_subpackage.test_file2"]
        importlib.invalidate_caches()

    def create_tree(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.folder_name)
        os.mkdir(self.folder_path)

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write(self.code)


class WhenRunningAPackageWithSubfolders:
    def establish_that_there_is_a_package_containing_subfolders(self):
        self.code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.folder_name = 'package4'
        self.tree = {
            "test_subfolder": ["test_file1"],
            "test_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()
        self.reporter = SpyReporter()


    def because_we_run_the_package(self):
        contexts.run(self.folder_path, [self.reporter])

    def it_should_import_the_file_in_the_test_folder(self):
        assert "test_file1" in sys.modules

    def it_should_not_import_the_file_in_the_test_folder_using_the_package_name(self):
        assert "package4.test_file1" not in sys.modules

    def it_should_run_the_file_in_the_test_folder(self):
        assert sys.modules["test_file1"].module_ran

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        assert "test_file3" not in sys.modules
        assert "package4.test_file3" not in sys.modules

    def it_should_import_the_test_package(self):
        assert "package4.test_subpackage" in sys.modules

    def it_should_only_import_the_test_package_using_its_full_name(self):
        assert "test_subpackage" not in sys.modules

    def it_should_run_the_test_package(self):
        assert sys.modules["package4.test_subpackage"].module_ran

    def it_should_import_the_file_in_the_test_package(self):
        assert "package4.test_subpackage.test_file2" in sys.modules

    def it_should_only_import_the_file_in_the_test_package_using_its_full_name(self):
        assert "test_file2" not in sys.modules
        assert "test_subpackage.test_file2" not in sys.modules

    def it_should_run_the_file_in_the_test_package(self):
        assert sys.modules["package4.test_subpackage.test_file2"].module_ran

    def it_should_not_import_the_non_test_package(self):
        assert "package4.another_subpackage" not in sys.modules

    def it_should_not_import_the_file_in_the_non_test_package(self):
        assert "package4.another_subpackage.test_file4" not in sys.modules
        assert "another_subpackage.test_file4" not in sys.modules
        assert "package4.test_file4" not in sys.modules
        assert "test_file4" not in sys.modules

    def it_should_not_import_any_init_files(self):
        assert "__init__" not in sys.modules
        assert "package4.__init__" not in sys.modules
        assert "test_subpackage.__init__" not in sys.modules
        assert "package4.test_subpackage.__init__" not in sys.modules
        assert "another_subpackage.__init__" not in sys.modules
        assert "package4.another_subpackage.__init__" not in sys.modules

    def it_should_call_suite_started_for_four_modules(self):
        assert self.reporter.calls[1][0] == 'suite_started'
        assert self.reporter.calls[7][0] == 'suite_started'
        assert self.reporter.calls[13][0] == 'suite_started'
        assert self.reporter.calls[19][0] == 'suite_started'

    def it_should_pass_the_suites_into_suite_started(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'package4', 'package4.test_subpackage', 'package4.test_subpackage.test_file2', 'test_file1'}

    def it_should_call_suite_ended_for_four_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'
        assert self.reporter.calls[24][0] == 'suite_ended'

    def it_should_pass_the_suites_into_suite_ended(self):
        names = {call[1].name for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'package4', 'package4.test_subpackage', 'package4.test_subpackage.test_file2', 'test_file1'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["package4.test_subpackage"]
        del sys.modules["package4.test_subpackage.test_file2"]
        importlib.invalidate_caches()

    def create_tree(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.folder_name)
        os.mkdir(self.folder_path)

        with open(os.path.join(self.folder_path, "__init__.py"), 'w+') as f:
            f.write(self.code)

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write(self.code)


class WhenRunningAFolderWithAFileThatFailsToImport:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.bad_code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True

raise TypeError("leave it aaaaht")
"""
        self.good_code = """
module_ran = False

class TestSpec:
    def it(self):
        global module_ran
        module_ran = True
"""
        self.module_names = ["test_file1", "test_file2"]
        self.create_folder()
        self.write_files()
        self.reporter = SpyReporter()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.reporter])

    def it_should_report_an_unexpected_error(self):
        assert self.reporter.calls[1][0] == "unexpected_error"

    def it_should_pass_in_an_exception(self):
        assert isinstance(self.reporter.calls[1][1], TypeError)

    def it_should_import_the_second_module(self):
        assert self.module_names[1] in sys.modules

    def it_should_run_the_second_module(self):
        assert sys.modules[self.module_names[1]].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_names[1]]
        importlib.invalidate_caches()

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'problematic_folder')
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n+".py") for n in self.module_names]
        with open(self.filenames[0], 'w+') as f:
            f.write(self.bad_code)
        with open(self.filenames[1], 'w+') as f:
            f.write(self.good_code)



if __name__ == "__main__":
    contexts.main()
