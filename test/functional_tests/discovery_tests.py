import collections.abc
import os
import shutil
import sys
import types
import contexts
from unittest import mock
from .tools import SpyReporter
from contexts.plugins import Plugin
from contexts.plugins.importing import Importer


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

    def it_should_pass_the_name_into_suite_started(self):
        assert self.reporter.calls[1][1] == self.module.__name__

    def it_should_call_suite_ended(self):
        assert self.reporter.calls[-2][0] == "suite_ended"

    def it_should_pass_the_name_into_suite_ended(self):
        assert self.reporter.calls[-2][1] == self.module.__name__


class WhenAPluginModifiesAClassList:
    def establish_that_a_plugin_is_fiddling_with_the_list(self):
        self.ran_reals = False
        class HasSpecInTheName:
            def it_should_run_this(s):
                self.ran_reals = True
        class HasWhenInTheName:
            def it_should_run_this(s):
                self.ran_reals = True

        self.ran_spies = []
        class NormalClass1:
            def it_should_run_this(s):
                self.ran_spies.append('NormalClass1')
        class NormalClass2:
            def it_should_run_this(s):
                self.ran_spies.append('NormalClass2')
        self.module = types.ModuleType('fake_specs')
        self.module.HasSpecInTheName = HasSpecInTheName
        self.module.HasWhenInTheName = HasWhenInTheName
        self.NormalClass1 = NormalClass1
        self.NormalClass2 = NormalClass2

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [NormalClass1, NormalClass2]
        self.plugin = mock.Mock()
        self.plugin.process_class_list = modify_list

    def because_we_run_the_module(self):
        contexts.run(self.module, [self.plugin])

    def it_should_pass_a_list_of_the_found_classes_into_process_class_list(self):
        assert isinstance(self.called_with, collections.abc.MutableSequence)
        assert set(self.called_with) == {self.module.HasSpecInTheName, self.module.HasWhenInTheName}

    def it_should_run_the_classes_in_the_list_that_the_plugin_modified(self):
        assert self.ran_spies == ['NormalClass1', 'NormalClass2']

    def it_should_not_run_the_old_version_of_the_list(self):
        assert not self.ran_reals


class WhenRunningAFile:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.write_file()
        self.reporter = SpyReporter()

        self.module = types.ModuleType(self.module_name)
        class When:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module.When = When

        self.not_implemented_plugin = mock.Mock(wraps=Plugin())
        del self.not_implemented_plugin.import_module

        self.noop_plugin = mock.Mock(wraps=Plugin())

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.return_value = self.module

        self.too_late_plugin = mock.Mock(spec=Plugin)

        self.plugin_master = mock.Mock()
        self.plugin_master.not_implemented_plugin = self.not_implemented_plugin
        self.plugin_master.noop_plugin = self.noop_plugin
        self.plugin_master.plugin = self.plugin
        self.plugin_master.too_late_plugin = self.too_late_plugin

    def because_we_run_the_file(self):
        contexts.run(self.filename, [
            self.not_implemented_plugin,
            self.noop_plugin,
            self.plugin,
            self.too_late_plugin
        ])

    def it_should_ask_the_plugins_to_import_the_correct_file(self):
        self.plugin_master.assert_has_calls([
            mock.call.noop_plugin.import_module(TEST_DATA_DIR, self.module_name),
            mock.call.plugin.import_module(TEST_DATA_DIR, self.module_name)
            ])

    @contexts.assertion
    def it_should_not_ask_any_plugins_after_the_one_that_returned(self):
        assert not self.too_late_plugin.import_module.called

    def it_should_run_the_module_that_the_plugin_imported(self):
        assert self.module.When.ran

    def it_should_call_suite_started_with_the_module_name(self):
        self.plugin.suite_started.assert_called_once_with(self.module_name)

    def it_should_call_suite_ended_with_the_module_name(self):
        self.plugin.suite_started.assert_called_once_with(self.module_name)

    def cleanup_the_file_system(self):
        os.remove(self.filename)

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenAPluginFailsToImportAModule:
    def establish_that_the_plugin_throws_an_exception(self):
        self.exception = Exception()
        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.side_effect = self.exception

        self.module_name = 'accident_prone_test_module'

        self.setup_filesystem()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_pass_the_exception_into_unexpected_error_on_the_plugin(self):
        self.plugin.unexpected_error.assert_called_once_with(self.exception)

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'plugin_failing_folder')
        os.mkdir(self.folder_path)

        filename = os.path.join(self.folder_path, self.module_name+".py")
        with open(filename, 'w+') as f:
            f.write("")


class WhenRunningAFolderWhichIsNotAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_names = ["test_file1", "test_file2", "an_innocent_module"]
        self.setup_filesystem()

        self.module1 = types.ModuleType(self.module_names[0])
        class Spec1:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module1.Spec1 = Spec1
        self.module2 = types.ModuleType(self.module_names[1])
        class Spec2:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module2.Spec2 = Spec2

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.side_effect = [self.module1, self.module2]

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_ask_the_plugin_to_import_the_correct_files(self):
        self.plugin.import_module.assert_has_calls([
            mock.call(self.folder_path, self.module_names[0]),
            mock.call(self.folder_path, self.module_names[1])
            ], any_order=True)

    def it_should_not_import_the_non_test_module(self):
        assert self.plugin.import_module.call_count == 2

    def it_should_run_the_first_module(self):
        assert self.module1.Spec1.ran

    def it_should_run_the_second_module(self):
        assert self.module2.Spec2.ran

    def it_should_call_suite_started_with_the_name_of_each_module(self):
        self.plugin.suite_started.assert_has_calls([
            mock.call(self.module1.__name__),
            mock.call(self.module2.__name__)
            ], any_order=True)

    def it_should_call_suite_ended_with_the_name_of_each_module(self):
        self.plugin.suite_ended.assert_has_calls([
            mock.call(self.module1.__name__),
            mock.call(self.module2.__name__)
            ], any_order=True)

    def it_should_end_the_first_suite_before_starting_the_second(self):
        self.plugin.assert_has_calls([
            mock.call.suite_ended(self.module1.__name__),
            mock.call.suite_started(self.module2.__name__),
            ])

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name+".py")
            with open(filename, 'w+') as f:
                f.write('')


class WhenPluginsModifyAModuleList:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_names = ["test_file1", "test_file2", "an_innocent_module"]
        self.setup_filesystem()

        self.ran_spies = []
        class SpySpecInModule1:
            def it_should_run_this(s):
                self.ran_spies.append('module1')
        class SpySpecInModule2:
            def it_should_run_this(s):
                self.ran_spies.append('module2')
        self.module1 = types.ModuleType('module1')
        self.module1.SpySpecInModule1 = SpySpecInModule1
        self.module2 = types.ModuleType('module2')
        self.module2.SpySpecInModule2 = SpySpecInModule2

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [self.module1, self.module2]
        self.plugin = mock.Mock()
        # if it tried to run strings as modules it would crash
        self.plugin.import_module.side_effect = ['x', 'y']
        self.plugin.process_module_list.side_effect = modify_list

        self.plugin2 = mock.Mock()

        self.plugin_master = mock.Mock()
        self.plugin_master.plugin = self.plugin
        self.plugin_master.plugin2 = self.plugin2

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin, self.plugin2])

    def it_should_ask_the_plugins_to_process_the_module_list_in_order(self):
        self.plugin_master.assert_has_calls([
            mock.call.plugin.process_module_list(mock.ANY),
            mock.call.plugin2.process_module_list(mock.ANY)
            ])

    def it_should_pass_the_imported_modules_in_to_the_first_plugin(self):
        assert self.called_with == ['x', 'y']

    def it_should_pass_the_modified_list_in_to_the_second_plugin(self):
        self.plugin2.process_module_list.assert_called_once_with([self.module1, self.module2])

    def it_should_run_the_modules_in_the_list_that_the_config_modified(self):
        assert self.ran_spies == ['module1', 'module2']

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def create_folder(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'shuffling_folder')
        os.mkdir(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name+".py")
            with open(filename, 'w+') as f:
                f.write('')


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
        contexts.run(self.folder_path, [Importer()])

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.package_name].is_fake

    def it_should_not_re_run_the_module(self):
        assert not sys.modules[self.package_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name]

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
        contexts.run(self.folder_path, [Importer()])

    def it_should_import_the_new_module_and_overwrite_the_old_one(self):
        assert not sys.modules[self.package_name].is_fake

    def it_should_run_the_first_module(self):
        assert sys.modules[self.package_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name]

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
        contexts.run(self.folder_path, [Importer()])

    def it_should_not_re_import_the_module(self):
        assert sys.modules[self.qualified_name].is_fake

    def it_should_not_re_run_the_module(self):
        assert not sys.modules[self.qualified_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.qualified_name]

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
        contexts.run(self.folder_path, [Importer()])

    def it_should_import_the_new_module_and_overwrite_the_old_one(self):
        assert not sys.modules[self.qualified_name].is_fake

    def it_should_run_the_first_module(self):
        assert sys.modules[self.qualified_name].module_ran

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.qualified_name]

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
        contexts.run(self.folder_path, [Importer(), self.reporter])

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

    def it_should_pass_the_names_into_suite_started(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'package_folder', 'package_folder.test_file1', 'package_folder.test_file2'}

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'

    def it_should_pass_the_names_into_suite_ended(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'package_folder', 'package_folder.test_file1', 'package_folder.test_file2'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name + '.' + self.module_names[1]]
        del sys.modules[self.package_name + '.' + self.module_names[2]]
        del sys.modules[self.package_name]

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
        contexts.run(self.folder_path, [Importer(), self.reporter])

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

    def it_should_pass_the_names_into_suite_started(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'test_file1', 'test_subpackage', 'test_subpackage.test_file2'}

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'

    def it_should_pass_the_names_into_suite_ended(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'test_file1', 'test_subpackage', 'test_subpackage.test_file2'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["test_subpackage"]
        del sys.modules["test_subpackage.test_file2"]

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
        contexts.run(self.folder_path, [Importer(), self.reporter])

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

    def it_should_pass_the_names_into_suite_started(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_started'}
        assert names == {'package4', 'package4.test_subpackage', 'package4.test_subpackage.test_file2', 'test_file1'}

    def it_should_call_suite_ended_for_four_modules(self):
        assert self.reporter.calls[6][0] == 'suite_ended'
        assert self.reporter.calls[12][0] == 'suite_ended'
        assert self.reporter.calls[18][0] == 'suite_ended'
        assert self.reporter.calls[24][0] == 'suite_ended'

    def it_should_pass_the_names_into_suite_ended(self):
        names = {call[1] for call in self.reporter.calls if call[0] == 'suite_ended'}
        assert names == {'package4', 'package4.test_subpackage', 'package4.test_subpackage.test_file2', 'test_file1'}

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["package4.test_subpackage"]
        del sys.modules["package4.test_subpackage.test_file2"]

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
        contexts.run(self.folder_path, [Importer(), self.reporter])

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
