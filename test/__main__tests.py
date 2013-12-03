import os
import sure
from contexts import __main__


class WhenParsingArguments:
    @classmethod
    def examples(cls):
        # do the defaults; try them individually; try them all together
        yield [], {'capture': True, 'verbose': False, 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['-s'], {'capture': False, 'verbose': False, 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--no-capture'], {'capture': False, 'verbose': False, 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['-v'], {'capture': True, 'verbose': True, 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--verbose'], {'capture': True, 'verbose': True, 'teamcity': False, 'shuffle': True, 'path': os.getcwd()}
        yield ['--teamcity'], {'capture': True, 'verbose': False, 'teamcity': True, 'shuffle': True, 'path': os.getcwd()}
        yield ['--no-random'], {'capture': True, 'verbose': False, 'teamcity': False, 'shuffle': False, 'path': os.getcwd()}
        yield ['my/fake/path'], {'capture': True, 'verbose': False, 'teamcity': False, 'shuffle': True, 'path': 'my/fake/path'}
        yield ['-sv', '--no-random', '--teamcity', 'another/made/up/location'], {
            'capture': False,
            'verbose': True,
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
        self.result.verbose.should.equal(self.expected['verbose'])

    def it_should_return_the_correct_value_for_teamcity(self):
        self.result.teamcity.should.equal(self.expected['teamcity'])

    def it_should_return_the_correct_value_for_shuffle(self):
        self.result.shuffle.should.equal(self.expected['shuffle'])

    def it_should_return_the_correct_path(self):
        self.result.path.should.equal(self.expected['path'])

