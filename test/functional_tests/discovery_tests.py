import collections.abc
import os
import shutil
import types
import contexts
from unittest import mock
from .tools import SpyReporter
from contexts.plugins import Plugin, TEST_FOLDER, CONTEXT, ASSERTION


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data")


class WhenAPluginChoosesClasses:
    def context(self):
        class ToRun1:
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class ToRun2:
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class NotToRun:
            was_instantiated = False
            def __init__(self):
                self.__class__.was_instantiated = True
        self.module = types.ModuleType('fake_specs')
        self.module.ToRun1 = ToRun1
        self.module.ToRun2 = ToRun2
        self.module.NotToRun = NotToRun

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.identify_class.side_effect = lambda cls: {
            ToRun1: CONTEXT,
            ToRun2: CONTEXT,
            NotToRun: None
        }[cls]
        self.plugin.identify_method.side_effect = lambda meth: {
            ToRun1.it_should_run_this: ASSERTION,
            ToRun2.it_should_run_this: ASSERTION,
        }[meth]
        self.other_plugin = mock.Mock()
        self.other_plugin.identify_class.return_value = None

    def because_we_run_the_module(self):
        contexts.run(self.module, [self.plugin, self.other_plugin])

    def it_should_run_the_class_the_plugin_likes(self):
        assert self.module.ToRun1.was_run

    def it_should_run_the_other_class_the_plugin_likes(self):
        assert self.module.ToRun2.was_run

    def it_should_only_ask_the_second_plugin_what_to_do_with_the_class_its_not_sure_about(self):
        self.other_plugin.identify_class.assert_called_once_with(self.module.NotToRun)

    def it_should_not_run_the_class_which_neither_plugin_wanted(self):
        assert not self.module.NotToRun.was_instantiated


class WhenAPluginModifiesAClassList:
    def establish_that_a_plugin_is_fiddling_with_the_list(self):
        self.ran_reals = False
        class FoundClass1:
            def it_should_run_this(s):
                self.ran_reals = True
        class FoundClass2:
            def it_should_run_this(s):
                self.ran_reals = True

        self.ran_spies = []
        class AnotherClass1:
            def it_should_run_this(s):
                self.ran_spies.append('AnotherClass1')
        class AnotherClass2:
            def it_should_run_this(s):
                self.ran_spies.append('AnotherClass2')
        self.module = types.ModuleType('fake_specs')
        self.module.FoundClass1 = FoundClass1
        self.module.FoundClass2 = FoundClass2
        self.AnotherClass1 = AnotherClass1
        self.AnotherClass2 = AnotherClass2

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [AnotherClass1, AnotherClass2]
        self.plugin = mock.Mock()
        self.plugin.process_class_list = modify_list
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_module(self):
        contexts.run(self.module, [self.plugin])

    def it_should_pass_a_list_of_the_found_classes_into_process_class_list(self):
        assert isinstance(self.called_with, collections.abc.MutableSequence)
        assert set(self.called_with) == {self.module.FoundClass1, self.module.FoundClass2}

    def it_should_run_the_classes_in_the_list_that_the_plugin_modified(self):
        assert self.ran_spies == ['AnotherClass1', 'AnotherClass2']

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
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

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


class WhenRunningAFileInAPackage:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.package_name = "package_with_one_file"
        self.full_module_name = self.package_name + '.' + self.module_name
        self.module_list = [types.ModuleType(self.package_name), types.ModuleType(self.full_module_name)]
        self.setup_tree()

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.side_effect = self.module_list

    def because_we_run_the_file(self):
        contexts.run(self.filename, [self.plugin])

    def it_should_import_the_package_before_the_file(self):
        assert self.plugin.import_module.call_args_list == [
            mock.call(TEST_DATA_DIR, self.package_name),
            mock.call(TEST_DATA_DIR, self.package_name + '.' + self.module_name)
        ]

    def it_should_discard_the_package_module(self):
        # it only needs to have been imported, not run
        self.plugin.process_module_list.assert_called_once_with(self.module_list[-1:])

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_location)

    def setup_tree(self):
        self.folder_location = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_location)

        self.filename = os.path.join(self.folder_location, self.module_name+".py")
        with open(os.path.join(self.folder_location, '__init__.py'), 'w+') as f:
            f.write('')
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenRunningAFileInASubPackage:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.package_name = "package_with_one_subpackage"
        self.subpackage_name = "subpackage_with_one_file"

        self.full_subpackage_name = self.package_name + '.' + self.subpackage_name
        self.full_module_name = self.full_subpackage_name + '.' + self.module_name

        self.module_list = [types.ModuleType(self.package_name), types.ModuleType(self.full_subpackage_name), types.ModuleType(self.full_module_name)]
        self.setup_tree()

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.side_effect = self.module_list

    def because_we_run_the_file(self):
        contexts.run(self.filename, [self.plugin])

    def it_should_import_the_package_before_the_file(self):
        assert self.plugin.import_module.call_args_list == [
            mock.call(TEST_DATA_DIR, self.package_name),
            mock.call(TEST_DATA_DIR, self.full_subpackage_name),
            mock.call(TEST_DATA_DIR, self.full_module_name)
        ]

    def it_should_discard_the_package_modules(self):
        self.plugin.process_module_list.assert_called_once_with(self.module_list[-1:])

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_location)

    def setup_tree(self):
        self.folder_location = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_location)
        subpackage_folder = os.path.join(self.folder_location, self.subpackage_name)
        os.mkdir(subpackage_folder)
        with open(os.path.join(self.folder_location, '__init__.py'), 'w+') as f:
            f.write('')
        with open(os.path.join(subpackage_folder, '__init__.py'), 'w+') as f:
            f.write('')

        self.filename = os.path.join(subpackage_folder, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenRunningInitDotPy:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.package_name = "package_with_one_file"
        self.setup_tree()

        self.module = types.ModuleType(self.package_name)

        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.import_module.return_value = self.module

    def because_we_run_the_file(self):
        contexts.run(self.filename, [self.plugin])

    def it_should_import_it_as_a_package(self):
        assert self.plugin.import_module.call_args_list == [
            mock.call(TEST_DATA_DIR, self.package_name)
        ]

    def it_should_not_discard_the_package_module(self):
        self.plugin.process_module_list.assert_called_once_with([self.module])

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_location)

    def setup_tree(self):
        self.folder_location = os.path.join(TEST_DATA_DIR, self.package_name)
        self.filename = os.path.join(self.folder_location, '__init__.py')
        os.mkdir(self.folder_location)
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
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

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
        class Spec1:
            def it_should_run_this(s):
                self.ran_spies.append('module1')
        class Spec2:
            def it_should_run_this(s):
                self.ran_spies.append('module2')
        self.module1 = types.ModuleType('module1')
        self.module1.Spec1 = Spec1
        self.module2 = types.ModuleType('module2')
        self.module2.Spec2 = Spec2

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [self.module1, self.module2]
        self.plugin = mock.Mock()
        # if it tried to run strings as modules it would crash
        self.plugin.import_module.side_effect = ['x', 'y']
        self.plugin.process_module_list.side_effect = modify_list
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

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

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name+".py")
            with open(filename, 'w+') as f:
                f.write('')


class WhenRunningAFolderWhichIsAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.package_name = 'package_folder'
        self.module_names = ["__init__", "test_file1", "test_file2", "an_innocent_module"]
        self.setup_filesystem()

        self.module1 = types.ModuleType(self.package_name)
        class Class1:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module1.Class1 = Class1
        self.module2 = types.ModuleType(self.package_name + '.' + self.module_names[1])
        class Class2:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module2.Class2 = Class2
        self.module3 = types.ModuleType(self.package_name + '.' + self.module_names[2])
        class Class3:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module3.Class3 = Class3

        self.plugin = mock.Mock()
        self.plugin.import_module.side_effect = [self.module1, self.module2, self.module3]
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_import_the_package_first(self):
        assert self.plugin.import_module.call_args_list[0] == mock.call(TEST_DATA_DIR, self.package_name)

    def it_should_import_both_submodules(self):
        self.plugin.import_module.assert_has_calls([
            mock.call(TEST_DATA_DIR, self.package_name + '.' + self.module_names[1]),
            mock.call(TEST_DATA_DIR, self.package_name + '.' + self.module_names[2])
        ], any_order=True)

    def it_should_run_the_package(self):
        assert self.module1.Class1.ran

    def it_should_run_the_first_module(self):
        assert self.module2.Class2.ran

    def it_should_run_the_second_module(self):
        assert self.module3.Class3.ran

    def it_should_call_suite_started_for_three_modules(self):
        assert self.plugin.suite_started.call_args_list == [
            mock.call(self.module1.__name__),
            mock.call(self.module2.__name__),
            mock.call(self.module3.__name__)
        ]

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.plugin.suite_ended.call_args_list == [
            mock.call(self.module1.__name__),
            mock.call(self.module2.__name__),
            mock.call(self.module3.__name__)
        ]

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name+".py")
            with open(filename, 'w+') as f:
                f.write('')


class WhenRunningAFolderWithSubfolders:
    def establish_that_there_is_a_folder_containing_subfolders(self):
        self.folder_name = 'folder3'
        self.tree = {
            "wanted_subfolder": ["test_file1"],
            "wanted_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

        def identify_folder(folder_path):
            if (folder_path == os.path.join(self.folder_path, "wanted_subfolder") or
                folder_path == os.path.join(self.folder_path, "wanted_subpackage")):
                return TEST_FOLDER
        self.plugin = mock.Mock(spec=Plugin)
        self.plugin.identify_folder.side_effect = identify_folder

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_import_the_file_in_the_test_folder(self):
        self.plugin.import_module.assert_any_call(os.path.join(self.folder_path, "wanted_subfolder"), "test_file1")

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        assert mock.call(mock.ANY, "test_file3") not in self.plugin.import_module.call_args_list

    def it_should_import_the_test_package_followed_by_the_test_submodule(self):
        self.plugin.import_module.assert_has_calls([
            mock.call(self.folder_path, "wanted_subpackage"),
            mock.call(self.folder_path, "wanted_subpackage.test_file2")
            ])

    def it_should_not_import_the_non_test_package(self):
        assert mock.call(mock.ANY, "another_subpackage") not in self.plugin.import_module.call_args_list

    def it_should_not_import_the_file_in_the_non_test_package(self):
        assert mock.call(mock.ANY, "another_subpackage.test_file4") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_file4") not in self.plugin.import_module.call_args_list

    def it_should_not_import_anything_called_init(self):
        assert mock.call(mock.ANY, "__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "wanted_subpackage.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "another_subpackage.__init__") not in self.plugin.import_module.call_args_list

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def create_tree(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.folder_name)
        os.mkdir(self.folder_path)

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write('')


class WhenRunningAPackageWithSubfolders:
    def establish_that_there_is_a_package_containing_subfolders(self):
        self.package_name = 'package4'
        self.tree = {
            "test_subfolder": ["test_file1"],
            "test_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

        self.plugin = mock.Mock()

    def because_we_run_the_package(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_import_the_package_first(self):
        assert self.plugin.import_module.call_args_list[0] == mock.call(TEST_DATA_DIR, self.package_name)

    def it_should_import_the_file_in_the_test_folder(self):
        self.plugin.import_module.assert_any_call(os.path.join(self.folder_path, "test_subfolder"), "test_file1")

    def it_should_not_import_the_file_in_the_test_folder_using_the_package_name(self):
        assert mock.call(mock.ANY, "package4.test_file1") not in self.plugin.import_module.call_args_list

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        assert mock.call(mock.ANY, "package4.test_file3") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_file3") not in self.plugin.import_module.call_args_list

    def it_should_import_the_test_subpackage_followed_by_the_test_submodule(self):
        self.plugin.import_module.assert_has_calls([
            mock.call(TEST_DATA_DIR, 'package4.test_subpackage'),
            mock.call(TEST_DATA_DIR, 'package4.test_subpackage.test_file2'),
        ])

    def it_should_only_import_the_test_package_using_its_full_name(self):
        assert mock.call(mock.ANY, "test_subpackage") not in self.plugin.import_module.call_args_list

    def it_should_only_import_the_test_submodule_using_its_full_name(self):
        assert mock.call(mock.ANY, "test_subpackage.test_file2") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_file2") not in self.plugin.import_module.call_args_list

    def it_should_not_import_the_non_test_package(self):
        assert mock.call(mock.ANY, "package4.another_subpackage") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "another_subpackage") not in self.plugin.import_module.call_args_list

    def it_should_not_import_the_file_in_the_non_test_package(self):
        assert mock.call(mock.ANY, "package4.another_subpackage.test_file4") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "another_subpackage.test_file4") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "package4.test_file4") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_file4") not in self.plugin.import_module.call_args_list

    def it_should_not_import_any_init_files(self):
        assert mock.call(mock.ANY, "__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "package4.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_subpackage.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "package4.test_subpackage.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "another_subpackage.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "package4.another_subpackage.__init__") not in self.plugin.import_module.call_args_list

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def create_tree(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

        with open(os.path.join(self.folder_path, "__init__.py"), 'w+') as f:
            f.write('')

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write('')


class WhenRunningAFolderWithAFileThatFailsToImport:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_names = ["test_file1", "test_file2"]
        self.setup_filesystem()

        self.module = types.ModuleType(self.module_names[1])
        class Spec:
            ran = False
            def it(self):
                self.__class__.ran = True
        self.module.Spec = Spec

        self.exception = Exception()
        self.plugin = mock.Mock()
        self.plugin.import_module.side_effect = [self.exception, self.module]

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, [self.plugin])

    def it_should_report_an_unexpected_error(self):
        self.plugin.unexpected_error.assert_called_once_with(self.exception)

    def it_should_still_import_the_second_module(self):
        assert self.plugin.import_module.call_count == 2

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'problematic_folder')
        os.mkdir(self.folder_path)

        self.filenames = [os.path.join(self.folder_path, n+".py") for n in self.module_names]
        with open(self.filenames[0], 'w+') as f:
            f.write('')
        with open(self.filenames[1], 'w+') as f:
            f.write('')



if __name__ == "__main__":
    contexts.main()
