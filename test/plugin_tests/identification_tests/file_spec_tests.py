from argparse import ArgumentParser
import io
from pathlib import PurePath
import tempfile

from contexts.plugin_interface import TEST_FOLDER, TEST_FILE
from contexts.plugins.identification.filespec import FileSpecIdentifier


class FileSpecContext:

    def given_a_temporary_directory(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def make_path(self, *args):
        parts = [self.tempdir.name]
        parts.extend(args)
        return str(PurePath(*parts))

    def cleanup_the_temp_dir(self):
        self.tempdir.cleanup()


class When_initialising_the_plugin_with_a_valid_command_line:

    def given_a_valid_command_line(self):
        self.cmd_line = "--specs=foo.txt"
        self.parser = ArgumentParser()

    def because_we_initialise_the_plugin(self):
        self.spec = FileSpecIdentifier()
        self.spec.setup_parser(self.parser)
        args = self.parser.parse_args(args=[self.cmd_line])
        self.result = self.spec.initialise(args, None)

    def it_should_have_initialised(self):
        assert(self.result is True)


class When_loading_the_specs_from_a_file(FileSpecContext):

    def given_a_valid_command_line(self):
        self.tempfile = self.make_path("specs.txt")

        # on linux we should write something like
        # /tmp/afhf293/acceptance-tests/carnivores/lion.py
        # under Windows we should write
        # c:\temp\djauey734\acceptance-tests\carnivores\lion.py
        self.testfile = self.make_path(
            "acceptance-tests",
            "carnivores",
            "lion.py")

        self.testdir = self.make_path("acceptance-tests")

        with io.open(self.tempfile, 'w') as f:
            f.write(self.testfile)
        self.cmd_line = "--specs="+self.tempfile

    def because_we_initialise_the_plugin(self):
        self.spec = FileSpecIdentifier()
        self.parser = ArgumentParser()
        self.spec.setup_parser(self.parser)
        args = self.parser.parse_args(args=[self.cmd_line])
        self.result = self.spec.initialise(args, None, cwd=self.tempdir.name)

    def it_should_have_initialised(self):
        assert(self.result is True)

    def it_should_identify_a_test_folder(self):
        assert(self.spec.identify_folder(self.testdir) == TEST_FOLDER)

    def it_should_identify_a_test_file(self):
        assert(self.spec.identify_file(self.testfile) == TEST_FILE)


class When_a_folder_is_listed_in_the_file_spec(FileSpecContext):

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance")
        self.spec = FileSpecIdentifier()
        self.testdir = self.make_path("acceptance")
        self.spec.initialise(file=file_spec, cwd=self.tempdir.name)

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder(self.testdir)

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_folder_is_not_listed_in_the_file_spec(FileSpecContext):

    def given_a_file_spec(self):
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=io.StringIO())
        self.testdir = self.make_path("acceptance")

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder(self.testdir)

    def it_should_not_identify_the_folder_for_tests(self):
        assert(self.result is None)


class When_a_folder_is_the_parent_of_an_item_in_the_spec(FileSpecContext):

    def given_a_file_spec(self):
        self.testdir = self.make_path("acceptance")
        testfile = self.make_path("acceptance", "herbivores", "cows.py")
        file_spec = io.StringIO(testfile)
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd=self.tempdir.name)

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder(self.testdir)

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_file_is_listed_in_the_spec(FileSpecContext):

    def given_a_file_spec(self):
        self.testfile = self.make_path("acceptance", "herbivores", "cows.py")
        file_spec = io.StringIO(self.testfile)
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd=self.tempdir.name)

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file(self.testfile)

    def it_should_identify_the_file_for_tests(self):
        assert(self.result is TEST_FILE)


class When_a_file_is_not_listed_in_the_spec(FileSpecContext):

    def given_a_file_spec(self):
        self.testfile = self.make_path("acceptance", "herbivores", "cows.py")
        file_spec = io.StringIO('')
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd=self.tempdir.name)

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file(
            self.testfile)

    def it_should_not_identify_the_file_for_tests(self):
        assert(self.result is None)
