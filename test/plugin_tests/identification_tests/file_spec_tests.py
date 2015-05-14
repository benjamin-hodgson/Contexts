from argparse import ArgumentParser
import io
from pathlib import PurePath
import tempfile

from contexts.plugin_interface import TEST_FOLDER, TEST_FILE
from contexts.plugins.identification.filespec import FileSpecIdentifier


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


class When_loading_the_specs_from_a_file:

    def given_a_valid_command_line(self):
        self.parser = ArgumentParser()
        self.tempfile = tempfile.NamedTemporaryFile(delete=False)
        self.cmd_line = "--specs="+self.tempfile.name
        self.tempfile.write(b'acceptance-tests/carnivores/lion.py\n')
        self.tempfile.flush()

    def because_we_initialise_the_plugin(self):
        self.spec = FileSpecIdentifier()
        self.spec.setup_parser(self.parser)
        args = self.parser.parse_args(args=[self.cmd_line])
        self.result = self.spec.initialise(args, None, cwd='/opt/contexts')

    def it_should_have_initialised(self):
        assert(self.result is True)

    def it_should_identify_a_test_folder(self):
        print(self.spec.specs)
        assert(self.spec.identify_folder('/opt/contexts/acceptance-tests') \
               == TEST_FOLDER)


    def it_should_identify_a_test_file(self):
        assert(self.spec.identify_file('/opt/contexts/acceptance-tests/carnivores/lion.py') \
               == TEST_FILE)

    def cleanup_the_file(self):
        self.tempfile.close()

class When_a_folder_is_listed_in_the_file_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance")
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_folder_is_not_listed_in_the_file_spec:

    def given_a_file_spec(self):
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=io.StringIO())

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_not_identify_the_folder_for_tests(self):
        assert(self.result is None)


class When_a_folder_is_the_parent_of_an_item_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/test_cows.py")
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_file_is_listed_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/cows.py")
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file("/opt/contexts/acceptance/herbivores/cows.py")

    def it_should_identify_the_file_for_tests(self):
        assert(self.result is TEST_FILE)


class When_a_file_is_not_listed_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/cows.py")
        self.spec = FileSpecIdentifier()
        self.spec.initialise(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file("/opt/contexts/acceptance/herbivores/goats.py")

    def it_should_not_identify_the_file_for_tests(self):
        assert(self.result is None)
