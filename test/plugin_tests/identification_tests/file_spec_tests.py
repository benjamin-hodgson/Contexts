import io
from pathlib import PurePath

from contexts.plugin_interface import TEST_FOLDER, TEST_FILE


class FileSpecIdentifier:

    def __init__(self, file=None, cwd=None):
        self.file = file
        self.cwd = cwd
        self._specs = None

    def identify_folder(self, folder):
        folder = PurePath(folder)
        for f in self.specs:
            if f == folder:
                return TEST_FOLDER
            if(folder in f.parents):
                return TEST_FOLDER

    def identify_file(self, file):
        file = PurePath(file)
        for f in self.specs:
            if(f == file):
                return TEST_FILE

    @property
    def specs(self):
        if(self._specs is None):
            self.read_from_file()
        return self._specs

    def read_from_file(self):
        if(self.file):
            self._specs = [PurePath(self.cwd, p) for p in self.file.readlines()]


class When_a_folder_is_listed_in_the_file_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance")
        self.spec = FileSpecIdentifier(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_folder_is_not_listed_in_the_file_spec:

    def given_a_file_spec(self):
        self.spec = FileSpecIdentifier(file=io.StringIO())

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_not_identify_the_folder_for_tests(self):
        assert(self.result is None)


class When_a_folder_is_the_parent_of_an_item_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/test_cows.py")
        self.spec = FileSpecIdentifier(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_folder(self):
        self.result = self.spec.identify_folder("/opt/contexts/acceptance")

    def it_should_identify_the_folder_for_tests(self):
        assert(self.result is TEST_FOLDER)


class When_a_file_is_listed_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/cows.py")
        self.spec = FileSpecIdentifier(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file("/opt/contexts/acceptance/herbivores/cows.py")

    def it_should_identify_the_file_for_tests(self):
        assert(self.result is TEST_FILE)



class When_a_file_is_not_listed_in_the_spec:

    def given_a_file_spec(self):
        file_spec = io.StringIO("acceptance/herbivores/cows.py")
        self.spec = FileSpecIdentifier(file=file_spec, cwd="/opt/contexts")

    def because_we_check_a_file(self):
        self.result = self.spec.identify_file("/opt/contexts/acceptance/herbivores/goats.py")

    def it_should_not_identify_the_file_for_tests(self):
        assert(self.result is None)
