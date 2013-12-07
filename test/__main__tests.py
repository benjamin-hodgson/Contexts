import os
import sys
import types
from io import StringIO
import sure
from contexts import __main__


class WhenParsingArguments:
    @classmethod
    def examples(cls):
        # do the defaults; try them individually; try them all together
        yield [], args_with()
        yield ['-s'], args_with(capture=False)
        yield ['--no-capture'], args_with(capture=False)
        yield ['-v'], args_with(verbosity='verbose')
        yield ['--verbose'], args_with(verbosity='verbose')
        yield ['-q'], args_with(verbosity='quiet')
        yield ['--quiet'], args_with(verbosity='quiet')
        yield ['--teamcity'], args_with(teamcity=True)
        yield ['--no-random'], args_with(shuffle=False)
        yield ['--no-colour'], args_with(colour=False)
        yield ['my/fake/path'], args_with(path='my/fake/path')
        yield (
            ['-sv','--no-random', '--teamcity', 'another/made/up/location'],
            args_with(capture=False, verbosity='verbose', teamcity=True, shuffle=False, path='another/made/up/location')
        )

    def establish_what_the_arguments_are(self, example):
        self.args, self.expected = example

        # argparse will try and print to stderr,
        # we don't want that to happen during the test run
        self.real_stderr = sys.stderr
        sys.stderr = StringIO()

    def because_we_parse_the_arguments(self):
        # argparse will try to quit if it fails
        # we don't want that to happen during the test run
        try:
            self.result = __main__.parse_args(self.args)
        except BaseException as e:
            pass

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

    def cleanup_stderr(self):
        sys.stderr = self.real_stderr


class WhenArgumentsSpecifyMutuallyExclusiveOptions:
    @classmethod
    def examples(cls):
        yield ['-q', '-v']
        yield ['--quiet', '--verbose']
        yield ['-q', '--verbose']
        yield ['--verbose', '-q']

    def establish_that_user_wants_verbose_and_quiet(self, example):
        self.args = example
        self.exception = None

        # argparse will try and print to stderr,
        # we don't want that to happen during the test run
        self.real_stderr = sys.stderr
        sys.stderr = StringIO()

    def because_we_try_to_parse_the_args(self):
        try:
            __main__.parse_args(self.args)
        except BaseException as e:
            self.exception = e

    def it_should_quit(self):
        self.exception.should.be.a('SystemExit')

    def cleanup_stderr(self):
        sys.stderr = self.real_stderr


class WhenCreatingReportersInQuietMode:
    def establish_that_the_args_specify_quiet_mode(self):
        self.args = types.SimpleNamespace(**args_with(verbosity='quiet'))

    def because_we_create_the_list_of_reporters(self):
        self.reporters = __main__.create_reporters(self.args)

    def it_should_return_a_reporter_with_a_stringio_output(self):
        self.reporters[0].stream.should_not.equal(sys.stdout)
        self.reporters[0].stream.should_not.equal(sys.stderr)
        self.reporters[0].stream.should.be.an('io.StringIO')

class WhenCreatingReportersWithNoColours:
    def establish_that_args_specify_no_colours(self):
        self.args = types.SimpleNamespace(**args_with(colour=False))

    def because_we_create_the_list_of_reporters(self):
        self.reporters = __main__.create_reporters(self.args)

    def none_of_them_should_be_coloured_reporters(self):
        for reporter in self.reporters:
            reporter.should_not.be.a('contexts.reporting.cli.ColouredReporter')


###########################################################
# Test helper methods
###########################################################

def args_with(**kwargs):
    defaults = {
        'capture': True,
        'verbosity': 'normal',
        'teamcity': False,
        'shuffle': True,
        'path': os.getcwd(),
        'colour': False
    }
    defaults.update(kwargs)
    return defaults
