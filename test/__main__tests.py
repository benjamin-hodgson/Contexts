import builtins
import os
import sys
import types
from io import StringIO
from unittest import mock
import sure
import contexts
from contexts import __main__
from contexts.reporting import cli


###########################################################
# Outside-in tests (good)
###########################################################

class WhenLoadingUpTheModule:
    # this test is just to balance
    # the fact that we're mocking it everywhere else
    def it_should_get_main_from_init(self):
        __main__.main.should.equal(contexts.main)

class MainSharedContext:
    def shared_context(self):
        self.real_main = __main__.main
        self.mock_main = __main__.main = mock.Mock()
        self.real_argv = sys.argv
        self.real_stdout = sys.stdout
        sys.stdout = mock.Mock()
        sys.stdout.isatty.return_value = True
        os.environ.pop("TEAMCITY_VERSION", None)

    def cleanup_main_and_argv_and_stdout(self):
        __main__.main = self.real_main
        sys.argv = self.real_argv
        sys.stdout = self.real_stdout

class WhenRunningFromCommandLineWithArguments(MainSharedContext):
    @classmethod
    def examples(self):
        yield [], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.ColouredSummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)
        yield ['-v'], (os.getcwd(), (cli.ColouredVerboseCapturingReporter(sys.stdout),), True)
        yield ['--verbose'], (os.getcwd(), (cli.ColouredVerboseCapturingReporter(sys.stdout),), True)
        yield ['--verbose', '--no-colour'], (os.getcwd(), (cli.StdOutCapturingReporter(sys.stdout),), True)
        yield ['--verbose', '--no-capture'], (os.getcwd(), (cli.ColouredVerboseReporter(sys.stdout),), True)
        yield ['--verbose', '--no-colour', '--no-capture'], (os.getcwd(), (cli.VerboseReporter(sys.stdout),), True)
        yield ['-vs'], (os.getcwd(), (cli.ColouredVerboseReporter(sys.stdout),), True)
        yield ['-q'], (os.getcwd(), (QuietReporterResemblance(),), True)
        yield ['--quiet'], (os.getcwd(), (QuietReporterResemblance(),), True)
        yield ['-s'], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.ColouredSummarisingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)
        yield ['--no-capture'], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.ColouredSummarisingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)
        yield ['--no-colour'], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.SummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)
        yield ['--no-capture', '--no-colour'], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.SummarisingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)
        yield ['--teamcity'], (os.getcwd(), (contexts.reporting.teamcity.TeamCityReporter(sys.stdout),), True)
        yield ['--no-random'], (os.getcwd(), (cli.DotsReporter(sys.stdout), cli.ColouredSummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), False)
        yield [os.path.join(os.getcwd(),'made','up','path')], (os.path.join(os.getcwd(),'made','up','path'), (cli.DotsReporter(sys.stdout), cli.ColouredSummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)), True)

    def establish_arguments(self, example):
        argv, self.expected = example
        sys.argv = ['run-contexts'] + argv

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_the_correct_arguments(self):
        self.mock_main.assert_called_once_with(*self.expected)

class WhenArgumentsSpecifyMutuallyExclusiveOptions(MainSharedContext):
    @classmethod
    def examples(cls):
        yield ['-q', '-v']
        yield ['-qv']
        yield ['--quiet', '--verbose']
        yield ['-q', '--verbose']
        yield ['--verbose', '-q']

    def establish_that_user_wants_verbose_and_quiet(self, example):
        sys.argv = ['run-contexts'] + example
        self.exception = None

        # argparse will try and print to stderr,
        # we don't want that to happen during the test run
        self.real_stderr = sys.stderr
        sys.stderr = StringIO()

    def because_we_run_from_cmd_line(self):
        try:
            __main__.cmd()
        except BaseException as e:
            self.exception = e

    def it_should_not_call_main(self):
        self.mock_main.mock_calls.should.be.empty

    def it_should_quit(self):
        self.exception.should.be.a('SystemExit')

    def cleanup_stderr_and_argv(self):
        sys.stderr = self.real_stderr


###########################################################
# Component tests (bad)
###########################################################

class WhenColoramaIsNotInstalled:
    def establish_that_colorama_raises_import_error(self):
        self.real_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "colorama":
                raise ImportError
            return self.real_import(name, *args, **kwargs)
        builtins.__import__ = fake_import

    def because_we_create_the_list_of_reporters(self):
        self.reporters = __main__.create_reporters(types.SimpleNamespace(**args_with()))

    def none_of_them_should_be_coloured_reporters(self):
        for reporter in self.reporters:
            reporter.should_not.be.a('contexts.reporting.cli.ColouredReporter')

    def cleanup_import(self):
        builtins.__import__ = self.real_import

class WhenStdOutIsAPipe:
    def establish_that_stdout_is_a_pipe(self):
        self.real_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: False

    def because_we_create_the_list_of_reporters(self):
        self.reporters = __main__.create_reporters(types.SimpleNamespace(**args_with()))

    def none_of_them_should_be_coloured_reporters(self):
        for reporter in self.reporters:
            reporter.should_not.be.a('contexts.reporting.cli.ColouredReporter')

    def cleanup_stdout(self):
        sys.stdout.isatty = self.real_isatty

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
        'colour': True
    }
    defaults.update(kwargs)
    return defaults

class QuietReporterResemblance(object):
    """
    Compares equal to quiet reporters
    """
    def __eq__(self, other):
        return type(other) == cli.StdOutCapturingReporter and other.stream != sys.stdout
