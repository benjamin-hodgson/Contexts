import os
import sys
import types
import sure
from contexts import __main__


class WhenParsingArguments:
    @classmethod
    def examples(cls):
        # do the defaults; try them individually; try them all together
        yield [], {'capture': True, 'verbosity': 'normal', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['-s'], {'capture': False, 'verbosity': 'normal', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--no-capture'], {'capture': False, 'verbosity': 'normal', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['-v'], {'capture': True, 'verbosity': 'verbose', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--verbose'], {'capture': True, 'verbosity': 'verbose', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['-q'], {'capture': True, 'verbosity': 'quiet', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--quiet'], {'capture': True, 'verbosity': 'quiet', 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--teamcity'], {'capture': True, 'verbosity': 'normal', 'teamcity': True, 'shuffle': True, 'path': os.getcwd()}
        yield ['--no-random'], {'capture': True, 'verbosity': 'normal', 'teamcity': False, 'shuffle': False, 'path': os.getcwd()}
        yield ['my/fake/path'], {'capture': True, 'verbosity': 'normal', 'teamcity': False, 'shuffle': True, 'path': 'my/fake/path'}
        yield ['-sv', '--no-random', '--teamcity', 'another/made/up/location'], {
            'capture': False,
            'verbosity': 'verbose',
            'teamcity': True,
            'shuffle': False,
            'path': 'another/made/up/location'
        }

    def establish_what_the_arguments_are(self, example):
        self.args, self.expected = example

    def because_we_parse_the_arguments(self):
        self.result = __main__.parse_args(self.args)

    def it_should_return_the_correct_value_for_no_capture(self):
        self.result.capture.should.equal(self.expected['capture'])

    def it_should_return_the_correct_value_for_verbose(self):
        self.result.verbosity.should.equal(self.expected['verbosity'])

    def it_should_return_the_correct_value_for_teamcity(self):
        self.result.teamcity.should.equal(self.expected['teamcity'])

    def it_should_return_the_correct_value_for_shuffle(self):
        self.result.shuffle.should.equal(self.expected['shuffle'])

    def it_should_return_the_correct_path(self):
        self.result.path.should.equal(self.expected['path'])


class WhenCreatingReportersInQuietMode:
    def establish_that_the_args_specify_quiet_mode(self):
        self.args = types.SimpleNamespace(verbosity='quiet', teamcity=False, capture=True)

    def because_we_create_the_list_of_reporters(self):
        self.reporters = __main__.create_reporters(self.args)

    def it_should_return_a_reporter_with_a_stringio_output(self):
        self.reporters[0].stream.should_not.equal(sys.stdout)
        self.reporters[0].stream.should.be.an('io.StringIO')
