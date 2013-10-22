import os
import shutil
import sys
import types
import sure
import contexts


class WhenRunningAModule(object):
    def context(self):
        class HasSpecInTheName(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class HasWhenInTheName(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class NormalClass(object):
            was_instantiated = False
            def __init__(self):
                self.__class__.was_instantiated = True
        self.module = types.ModuleType('fake_specs')
        self.module.HasSpecInTheName = HasSpecInTheName
        self.module.HasWhenInTheName = HasWhenInTheName
        self.module.NormalClass = NormalClass

    def because_we_run_the_module(self):
        contexts.run(self.module, contexts.core.Result())

    def it_should_run_the_spec(self):
        self.module.HasSpecInTheName.was_run.should.be.true

    def it_should_run_the_other_spec(self):
        self.module.HasWhenInTheName.was_run.should.be.true

    def it_should_not_instantiate_the_normal_class(self):
        self.module.NormalClass.was_instantiated.should.be.false

class WhenRunningAFile(object):
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.module_name = "test_file"
        self.create_folder()
        self.write_file()

    def because_we_run_the_file(self):
        contexts.run(self.filename, contexts.core.Result())

    def it_should_import_the_file(self):
        sys.modules.should.contain(self.module_name)

    def it_should_run_the_specs(self):
        sys.modules[self.module_name].module_ran.should.be.true

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_name]

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), 'data')
        os.mkdir(self.folder_path)

    def write_file(self):
        self.filename = os.path.join(self.folder_path, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)

class WhenRunningAFolderWhichIsNotAPackage(object):
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.module_names = ["test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_first_module(self):
        sys.modules.should.contain(self.module_names[0])

    def it_should_import_the_second_module(self):
        sys.modules.should.contain(self.module_names[1])

    def it_should_run_the_first_module(self):
        sys.modules[self.module_names[0]].module_ran.should.be.true

    def it_should_run_the_second_module(self):
        sys.modules[self.module_names[1]].module_ran.should.be.true

    def it_should_not_run_the_non_test_module(self):
        sys.modules.should_not.contain(self.module_names[2])

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.module_names[0]]
        del sys.modules[self.module_names[1]]

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), 'non_package_folder')
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n+".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)

class WhenRunningAFolderWhichIsAPackage(object):
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.package_name = 'package_folder'
        self.module_names = ["__init__", "test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_package(self):
        sys.modules.should.contain(self.package_name)

    def it_should_import_the_first_module(self):
        sys.modules.should.contain(self.package_name + '.' + self.module_names[1])

    def it_should_only_import_the_first_module_using_its_full_name(self):
        sys.modules.should_not.contain(self.module_names[1])

    def it_should_import_the_second_module(self):
        sys.modules.should.contain(self.package_name + '.' + self.module_names[2])

    def it_should_only_import_the_second_module_using_its_full_name(self):
        sys.modules.should_not.contain(self.module_names[1])

    def it_should_not_import_the_third_module(self):
        sys.modules.should_not.contain(self.package_name + '.' + self.module_names[3])
        sys.modules.should_not.contain(self.module_names[3])

    def it_should_not_import_init(self):
        sys.modules.should_not.contain("__init__")
        sys.modules.should_not.contain("package_folder.__init__")

    def it_should_run_the_package(self):
        sys.modules[self.package_name].module_ran.should.be.true

    def it_should_run_the_first_module(self):
        sys.modules[self.package_name + '.' + self.module_names[1]].module_ran.should.be.true

    def it_should_run_the_second_module(self):
        sys.modules[self.package_name + '.' + self.module_names[2]].module_ran.should.be.true

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules[self.package_name + '.' + self.module_names[1]]
        del sys.modules[self.package_name + '.' + self.module_names[2]]
        del sys.modules[self.package_name]

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n + ".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)

class WhenRunningAFolderWithSubfolders(object):
    def establish_that_there_is_a_folder_containing_subfolders(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.folder_name = 'folder3'
        self.tree = {
            "test_subfolder": ["test_file1"],
            "test_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_file_in_the_test_folder(self):
        sys.modules.should.contain("test_file1")

    def it_should_run_the_file_in_the_test_folder(self):
        sys.modules["test_file1"].module_ran.should.be.true

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        sys.modules.should_not.contain("test_file3")

    def it_should_import_the_test_package(self):
        sys.modules.should.contain("test_subpackage")

    def it_should_run_the_test_package(self):
        sys.modules["test_subpackage"].module_ran.should.be.true

    def it_should_import_the_file_in_the_test_package(self):
        sys.modules.should.contain("test_subpackage.test_file2")

    def it_should_only_import_the_file_in_the_test_package_using_its_full_name(self):
        sys.modules.should_not.contain("test_file2")

    def it_should_run_the_file_in_the_test_package(self):
        sys.modules["test_subpackage.test_file2"].module_ran.should.be.true

    def it_should_not_import_the_non_test_package(self):
        sys.modules.should_not.contain("another_subpackage")

    def it_should_not_import_the_file_in_the_non_test_package(self):
        sys.modules.should_not.contain("another_subpackage.test_file4")
        sys.modules.should_not.contain("test_file4")

    def it_should_not_import_any_init_files(self):
        sys.modules.should_not.contain("__init__")
        sys.modules.should_not.contain("test_subpackage.__init__")
        sys.modules.should_not.contain("another_subpackage.__init__")

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["test_subpackage"]
        del sys.modules["test_subpackage.test_file2"]

    def create_tree(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), self.folder_name)
        os.mkdir(self.folder_path)

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write(self.code)

class WhenRunningAPackageWithSubfolders(object):
    def establish_that_there_is_a_package_containing_subfolders(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.folder_name = 'package4'
        self.tree = {
            "test_subfolder": ["test_file1"],
            "test_subpackage": ["__init__", "test_file2"],
            "another_subfolder": ["test_file3"],
            "another_subpackage": ["__init__", "test_file4"]
        }
        self.create_tree()

    def because_we_run_the_package(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_file_in_the_test_folder(self):
        sys.modules.should.contain("test_file1")

    def it_should_not_import_the_file_in_the_test_folder_using_the_package_name(self):
        sys.modules.should_not.contain("package4.test_file1")

    def it_should_run_the_file_in_the_test_folder(self):
        sys.modules["test_file1"].module_ran.should.be.true

    def it_should_not_import_the_file_in_the_non_test_folder(self):
        sys.modules.should_not.contain("test_file3")
        sys.modules.should_not.contain("package4.test_file3")

    def it_should_import_the_test_package(self):
        sys.modules.should.contain("package4.test_subpackage")

    def it_should_only_import_the_test_package_using_its_full_name(self):
        sys.modules.should_not.contain("test_subpackage")

    def it_should_run_the_test_package(self):
        sys.modules["package4.test_subpackage"].module_ran.should.be.true

    def it_should_import_the_file_in_the_test_package(self):
        sys.modules.should.contain("package4.test_subpackage.test_file2")

    def it_should_only_import_the_file_in_the_test_package_using_its_full_name(self):
        sys.modules.should_not.contain("test_file2")
        sys.modules.should_not.contain("test_subpackage.test_file2")

    def it_should_run_the_file_in_the_test_package(self):
        sys.modules["package4.test_subpackage.test_file2"].module_ran.should.be.true

    def it_should_not_import_the_non_test_package(self):
        sys.modules.should_not.contain("package4.another_subpackage")

    def it_should_not_import_the_file_in_the_non_test_package(self):
        sys.modules.should_not.contain("package4.another_subpackage.test_file4")
        sys.modules.should_not.contain("another_subpackage.test_file4")
        sys.modules.should_not.contain("package4.test_file4")
        sys.modules.should_not.contain("test_file4")

    def it_should_not_import_any_init_files(self):
        sys.modules.should_not.contain("__init__")
        sys.modules.should_not.contain("package4.__init__")
        sys.modules.should_not.contain("test_subpackage.__init__")
        sys.modules.should_not.contain("package4.test_subpackage.__init__")
        sys.modules.should_not.contain("another_subpackage.__init__")
        sys.modules.should_not.contain("package4.another_subpackage.__init__")

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        shutil.rmtree(self.folder_path)
        del sys.modules["test_file1"]
        del sys.modules["package4.test_subpackage"]
        del sys.modules["package4.test_subpackage.test_file2"]

    def create_tree(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), self.folder_name)
        os.mkdir(self.folder_path)

        with open(os.path.join(self.folder_path, "__init__.py"), 'w+') as f:
            f.write(self.code)

        for subfolder in self.tree:
            folder_path = os.path.join(self.folder_path, subfolder)
            os.mkdir(folder_path)
            for module_name in self.tree[subfolder]:
                with open(os.path.join(folder_path, module_name) + ".py", 'w+') as f:
                    f.write(self.code)


if __name__ == "__main__":
    contexts.main()
