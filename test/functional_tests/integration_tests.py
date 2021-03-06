import os
import shutil
import types
import contexts
from unittest import mock
from .tools import UnorderedList, run_object
from contexts.plugin_interface import PluginInterface, TEST_FOLDER, TEST_FILE, CONTEXT, ASSERTION
from contexts import assertion


THIS_FILE = os.path.realpath(__file__)
TEST_DATA_DIR = os.path.join(os.path.dirname(THIS_FILE), "test_data")


class WhenAPluginSuppliesAFileToRun:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.write_file()

        self.module = types.ModuleType(self.module_name)
        self.ran = False

        class When:
            def it(s):
                self.ran = True
        self.module.When = When

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.get_object_to_run.return_value = self.filename
        self.plugin.import_module.return_value = self.module
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_with_the_plugin(self):
        contexts.run_with_plugins([self.plugin])

    def it_should_run_the_spec_in_the_file(self):
        assert self.ran

    def cleanup_the_file_system(self):
        os.remove(self.filename)

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenRunningAFile:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.write_file()

        self.module = types.ModuleType(self.module_name)

        class When:
            ran = False

            def it(self):
                self.__class__.ran = True
        self.module.When = When

        self.not_implemented_plugin = mock.Mock(wraps=PluginInterface())
        del self.not_implemented_plugin.import_module

        self.noop_plugin = mock.Mock(wraps=PluginInterface())

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.import_module.return_value = self.module
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

        self.too_late_plugin = mock.Mock(spec=PluginInterface)

        self.plugin_master = mock.Mock()
        self.plugin_master.not_implemented_plugin = self.not_implemented_plugin
        self.plugin_master.noop_plugin = self.noop_plugin
        self.plugin_master.plugin = self.plugin
        self.plugin_master.too_late_plugin = self.too_late_plugin

    def because_we_run_the_file(self):
        run_object(self.filename, [
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

    @assertion
    def it_should_not_ask_any_plugins_after_the_one_that_returned(self):
        assert not self.too_late_plugin.import_module.called

    def it_should_run_the_module_that_the_plugin_imported(self):
        assert self.module.When.ran

    def it_should_call_suite_started_with_the_module(self):
        self.plugin.suite_started.assert_called_once_with(self.module)

    def it_should_call_suite_ended_with_the_module(self):
        self.plugin.suite_started.assert_called_once_with(self.module)

    def cleanup_the_file_system(self):
        os.remove(self.filename)

    def write_file(self):
        self.filename = os.path.join(TEST_DATA_DIR, self.module_name + ".py")
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenRunningAFileInAPackage:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.module_name = "test_file"
        self.package_name = "package_with_one_file"
        self.full_module_name = self.package_name + '.' + self.module_name
        self.module_list = [types.ModuleType(self.package_name), types.ModuleType(self.full_module_name)]
        self.setup_tree()

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.import_module.side_effect = self.module_list

    def because_we_run_the_file(self):
        run_object(self.filename, [self.plugin])

    def it_should_import_the_package_before_the_file(self):
        assert self.plugin.import_module.call_args_list == [
            mock.call(TEST_DATA_DIR, self.package_name),
            mock.call(TEST_DATA_DIR, self.package_name + '.' + self.module_name)
        ]

    def it_should_not_ask_permission_to_import_the_package(self):
        assert not self.plugin.identify_folder.called

    def it_should_discard_the_package_module(self):
        # it only needs to have been imported, not run
        self.plugin.process_module_list.assert_called_once_with(self.module_list[-1:])

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_location)

    def setup_tree(self):
        self.folder_location = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_location)

        self.filename = os.path.join(self.folder_location, self.module_name + ".py")
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

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.import_module.side_effect = self.module_list

    def because_we_run_the_file(self):
        run_object(self.filename, [self.plugin])

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

        self.filename = os.path.join(subpackage_folder, self.module_name + ".py")
        with open(self.filename, 'w+') as f:
            f.write('')


class WhenRunningInitDotPy:
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.package_name = "package_with_one_file"
        self.setup_tree()

        self.module = types.ModuleType(self.package_name)

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.import_module.return_value = self.module

    def because_we_run_the_file(self):
        run_object(self.filename, [self.plugin])

    def it_should_import_it_as_a_package(self):
        self.plugin.import_module.assert_called_once_with(TEST_DATA_DIR, self.package_name)

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
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.import_module.side_effect = self.exception

        self.module_name = 'accident_prone_test_module'

        self.setup_filesystem()

    def because_we_run_the_folder(self):
        run_object(self.filename, [self.plugin])

    def it_should_pass_the_exception_into_unexpected_error_on_the_plugin(self):
        self.plugin.unexpected_error.assert_called_once_with(self.exception)

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'plugin_failing_folder')
        os.mkdir(self.folder_path)

        self.filename = os.path.join(self.folder_path, self.module_name + ".py")
        with open(self.filename, 'w+') as f:
            f.write("")


class WhenAPluginSuppliesAFolderToRun:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_name = "wanted_file1"
        self.setup_filesystem()

        self.ran = False
        self.module = types.ModuleType(self.module_name)

        class Class:
            def it(s):
                self.ran = True

        self.module.Class = Class

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.get_object_to_run.return_value = self.folder_path
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.import_module.return_value = self.module
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_with_the_plugin(self):
        contexts.run_with_plugins([self.plugin])

    def it_should_run_the_file(self):
        assert self.ran

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

        filename = os.path.join(self.folder_path, self.module_name + ".py")
        with open(filename, 'w+') as f:
            f.write('')


class WhenRunningAFolderWhichIsNotAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_names = ["wanted_file1", "wanted_file2", "an_innocent_module"]
        self.setup_filesystem()

        self.module1 = types.ModuleType(self.module_names[0])

        class Class1:
            ran = False

            def it(self):
                self.__class__.ran = True

        self.module1.Class1 = Class1
        self.module2 = types.ModuleType(self.module_names[1])

        class Class2:
            ran = False

            def it(self):
                self.__class__.ran = True

        self.module2.Class2 = Class2

        def identify_file(path):
            if (path == os.path.join(self.folder_path, self.module_names[0] + '.py') or
                path == os.path.join(self.folder_path, self.module_names[1] + '.py')):  # noqa
                return TEST_FILE

        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_file.side_effect = identify_file
        self.plugin.import_module.side_effect = [self.module1, self.module2]
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_folder(self):
        run_object(self.folder_path, [self.plugin])

    def it_should_not_ask_permission_to_run_the_folder(self):
        assert not self.plugin.identify_folder.called

    def it_should_ask_the_plugin_to_import_the_correct_files(self):
        assert self.plugin.import_module.call_args_list == UnorderedList([
            mock.call(self.folder_path, self.module_names[0]),
            mock.call(self.folder_path, self.module_names[1])
        ])

    def it_should_not_import_the_non_test_module(self):
        assert self.plugin.import_module.call_count == 2

    def it_should_run_the_first_module(self):
        assert self.module1.Class1.ran

    def it_should_run_the_second_module(self):
        assert self.module2.Class2.ran

    def it_should_call_suite_started_with_the_name_of_each_module(self):
        self.plugin.suite_started.assert_has_calls([
            mock.call(self.module1),
            mock.call(self.module2)
        ], any_order=True)

    def it_should_call_suite_ended_with_the_name_of_each_module(self):
        self.plugin.suite_ended.assert_has_calls([
            mock.call(self.module1),
            mock.call(self.module2)
        ], any_order=True)

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'non_package_folder')
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name + ".py")
            with open(filename, 'w+') as f:
                f.write('')


class WhenPluginsModifyAModuleList:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.module_names = ["wanted_file1", "wanted_file2"]
        self.setup_filesystem()

        self.ran_spies = []

        class Class1:
            def it_should_run_this(s):
                self.ran_spies.append('module1')

        class Class2:
            def it_should_run_this(s):
                self.ran_spies.append('module2')

        self.module1 = types.ModuleType('module1')
        self.module1.Class1 = Class1
        self.module2 = types.ModuleType('module2')
        self.module2.Class2 = Class2

        def modify_list(l):
            self.called_with = l.copy()
            l[:] = [self.module1, self.module2]
        self.plugin = mock.Mock()
        # if it tried to run strings as modules it would crash
        self.plugin.import_module.side_effect = ['x', 'y']
        self.plugin.process_module_list.side_effect = modify_list
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

        self.plugin2 = mock.Mock()

        self.plugin_master = mock.Mock()
        self.plugin_master.plugin = self.plugin
        self.plugin_master.plugin2 = self.plugin2

    def because_we_run_the_folder(self):
        run_object(self.folder_path, [self.plugin, self.plugin2])

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
            filename = os.path.join(self.folder_path, module_name + ".py")
            with open(filename, 'w+') as f:
                f.write('')


class WhenRunningAFolderWhichIsAPackage:
    def establish_that_there_is_a_folder_containing_modules(self):
        self.package_name = 'package_folder'
        self.module_names = ["__init__", "test_file1", "test_file2"]
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
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.identify_class.return_value = CONTEXT
        self.plugin.identify_method.return_value = ASSERTION

    def because_we_run_the_folder(self):
        run_object(self.folder_path, [self.plugin])

    def it_should_import_the_package_first(self):
        assert self.plugin.import_module.call_args_list[0] == mock.call(TEST_DATA_DIR, self.package_name)

    def it_should_not_ask_permission_to_import_the_package(self):
        assert not self.plugin.identify_folder.called

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
            mock.call(self.module1),
            mock.call(self.module2),
            mock.call(self.module3)
        ]

    def it_should_call_suite_ended_for_three_modules(self):
        assert self.plugin.suite_ended.call_args_list == [
            mock.call(self.module1),
            mock.call(self.module2),
            mock.call(self.module3)
        ]

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, self.package_name)
        os.mkdir(self.folder_path)

        for module_name in self.module_names:
            filename = os.path.join(self.folder_path, module_name + ".py")
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
                folder_path == os.path.join(self.folder_path, "wanted_subpackage")):  # noqa
                return TEST_FOLDER
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.identify_folder.side_effect = identify_folder

    def because_we_run_the_folder(self):
        run_object(self.folder_path, [self.plugin])

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
            "wanted_subfolder": ["test_file1"],
            "wanted_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

        def identify_folder(folder_path):
            if (folder_path == os.path.join(self.folder_path, "wanted_subfolder") or
                folder_path == os.path.join(self.folder_path, "wanted_subpackage")):  # noqa
                return TEST_FOLDER
        self.plugin = mock.Mock(spec=PluginInterface)
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.identify_folder.side_effect = identify_folder

    def because_we_run_the_package(self):
        run_object(self.folder_path, [self.plugin])

    def it_should_import_the_package_first(self):
        assert self.plugin.import_module.call_args_list[0] == mock.call(TEST_DATA_DIR, self.package_name)

    def it_should_not_ask_permission_to_import_the_package(self):
        assert mock.call(self.folder_path) not in self.plugin.identify_folder.call_args_list

    def it_should_import_the_file_in_the_test_folder(self):
        self.plugin.import_module.assert_any_call(os.path.join(self.folder_path, "wanted_subfolder"), "test_file1")

    def it_should_not_import_the_file_in_the_test_folder_using_the_package_name(self):
        assert mock.call(mock.ANY, "package4.test_file1") not in self.plugin.import_module.call_args_list

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        assert mock.call(mock.ANY, "package4.test_file3") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "test_file3") not in self.plugin.import_module.call_args_list

    def it_should_import_the_test_subpackage_followed_by_the_test_submodule(self):
        self.plugin.import_module.assert_has_calls([
            mock.call(TEST_DATA_DIR, 'package4.wanted_subpackage'),
            mock.call(TEST_DATA_DIR, 'package4.wanted_subpackage.test_file2'),
        ])

    def it_should_only_import_the_test_package_using_its_full_name(self):
        assert mock.call(mock.ANY, "wanted_subpackage") not in self.plugin.import_module.call_args_list

    def it_should_only_import_the_test_submodule_using_its_full_name(self):
        assert mock.call(mock.ANY, "wanted_subpackage.test_file2") not in self.plugin.import_module.call_args_list
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
        assert mock.call(mock.ANY, "wanted_subpackage.__init__") not in self.plugin.import_module.call_args_list
        assert mock.call(mock.ANY, "package4.wanted_subpackage.__init__") not in self.plugin.import_module.call_args_list
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
        self.plugin.identify_file.return_value = TEST_FILE
        self.plugin.import_module.side_effect = [self.exception, self.module]

    def because_we_run_the_folder(self):
        run_object(self.folder_path, [self.plugin])

    def it_should_report_an_unexpected_error(self):
        self.plugin.unexpected_error.assert_called_once_with(self.exception)

    def it_should_still_import_the_second_module(self):
        assert self.plugin.import_module.call_count == 2

    def cleanup_the_file_system(self):
        shutil.rmtree(self.folder_path)

    def setup_filesystem(self):
        self.folder_path = os.path.join(TEST_DATA_DIR, 'problematic_folder')
        os.mkdir(self.folder_path)

        self.filenames = [os.path.join(self.folder_path, n + ".py") for n in self.module_names]
        with open(self.filenames[0], 'w+') as f:
            f.write('')
        with open(self.filenames[1], 'w+') as f:
            f.write('')


class WhenRunningASubpackage:
    def establish_a_subpackage(self):
        self.package_name = 'running_a_subpackage'
        self.expected_pkg_name = "wanted_subpackage"
        self.other_pkg_name = "another_subpackage"
        self.tree = {
            self.expected_pkg_name: ["__init__"],
            self.other_pkg_name: ["__init__"]
        }
        self.create_tree()

        self.plugin = mock.Mock()
        self.plugin.identify_file.return_value = TEST_FILE
        self.expected_module = types.ModuleType(self.expected_pkg_name)
        self.plugin.import_module.side_effect = [types.ModuleType(self.package_name), self.expected_module]

    def because_we_run_the_subpackage(self):
        run_object(os.path.join(self.folder_path, self.expected_pkg_name), [self.plugin])

    def it_should_import_the_top_package_first(self):
        assert self.plugin.import_module.call_args_list[0] == mock.call(TEST_DATA_DIR, self.package_name)

    def it_should_import_the_subpackage_we_asked_for(self):
        assert self.plugin.import_module.call_args_list[1] == mock.call(TEST_DATA_DIR, self.package_name + '.' + self.expected_pkg_name)

    def it_should_not_import_anything_else(self):
        assert len(self.plugin.import_module.call_args_list) == 2

    # FIXME: this test fails
    # def it_should_only_run_the_module_we_asked_for(self):
    #     self.plugin.process_module_list.assert_called_once_with([self.expected_module])

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


if __name__ == "__main__":
    contexts.main()
