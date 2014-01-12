import builtins
import os
import sys
from io import StringIO
from unittest import mock
import colorama
import contexts
from contexts import __main__
from contexts.plugins import cli
from contexts.plugins.other import Shuffler


class WhenLoadingUpTheModule:
    # this test is just to balance
    # the fact that we're mocking it everywhere else
    def it_should_get_main_from_init(self):
        assert __main__.main is contexts.main


class MainSharedContext:
    def shared_context(self):
        self.real_colorama_init = colorama.init
        colorama.init = mock.Mock()
        self.real_main = __main__.main
        self.mock_main = __main__.main = mock.Mock()
        self.real_argv = sys.argv
        self.real_isatty = sys.stdout.isatty

        sys.argv = ['run-contexts']
        sys.stdout.isatty = lambda: True
        os.environ.pop("TEAMCITY_VERSION", None)

    def cleanup(self):
        __main__.main = self.real_main
        sys.argv = self.real_argv
        sys.stdout.isatty = self.real_isatty
        colorama.init = self.real_colorama_init


class WhenRunningFromCommandLineWithArguments(MainSharedContext):
    @classmethod
    def examples(self):
        yield [], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.ColouredSummarisingCapturingReporter, cli.TimedReporter), True]
        path = os.path.join(os.getcwd(),'made','up','path')
        yield [path], [path, (Shuffler, cli.DotsReporter, cli.ColouredSummarisingCapturingReporter, cli.TimedReporter), True]
        yield ['-v'], [os.getcwd(), (Shuffler, cli.ColouredVerboseCapturingReporter, cli.TimedReporter), True]
        yield ['--verbose'], [os.getcwd(), (Shuffler, cli.ColouredVerboseCapturingReporter, cli.TimedReporter), True]
        yield ['--verbose', '--no-colour'], [os.getcwd(), (Shuffler, cli.StdOutCapturingReporter, cli.TimedReporter), True]
        yield ['--verbose', '--no-capture'], [os.getcwd(), (Shuffler, cli.ColouredVerboseReporter, cli.TimedReporter), True]
        yield ['--verbose', '--no-colour', '--no-capture'], [os.getcwd(), (Shuffler, cli.VerboseReporter, cli.TimedReporter), True]
        yield ['-vs'], [os.getcwd(), (Shuffler, cli.ColouredVerboseReporter, cli.TimedReporter), True]
        yield ['-q'], [os.getcwd(), (Shuffler, QuietReporterResemblance), True]
        yield ['--quiet'], [os.getcwd(), (Shuffler, QuietReporterResemblance), True]
        yield ['-s'], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.ColouredSummarisingReporter, cli.TimedReporter), True]
        yield ['--no-capture'], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.ColouredSummarisingReporter, cli.TimedReporter), True]
        yield ['--no-colour'], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.SummarisingCapturingReporter, cli.TimedReporter), True]
        yield ['--no-capture', '--no-colour'], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.SummarisingReporter, cli.TimedReporter), True]
        yield ['--no-assert'], [os.getcwd(), (Shuffler, cli.DotsReporter, cli.ColouredSummarisingCapturingReporter, cli.TimedReporter), False]
        yield ['--teamcity'], [os.getcwd(), (Shuffler, contexts.plugins.teamcity.TeamCityReporter,), True]
        yield ['--no-random'], [os.getcwd(), (cli.DotsReporter, cli.ColouredSummarisingCapturingReporter, cli.TimedReporter), True]

    def establish_arguments(self, argv, expected):
        expected_reporters = []
        for cls in expected[1]:
            try:
                expected_reporters.append(cls(sys.stdout))
            except TypeError:
                expected_reporters.append(cls())
        self.expected = (expected[0], expected_reporters, expected[2])
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

    def establish_that_user_wants_verbose_and_quiet(self, argv):
        sys.argv = ['run-contexts'] + argv
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
        assert not self.mock_main.called

    def it_should_quit(self):
        assert isinstance(self.exception, SystemExit)

    def cleanup_stderr_and_argv(self):
        sys.stderr = self.real_stderr


class WhenColoramaIsNotInstalled(MainSharedContext):
    def establish_that_colorama_raises_import_error(self):
        self.real_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "colorama":
                raise ImportError
            return self.real_import(name, *args, **kwargs)
        builtins.__import__ = fake_import

    def because_we_run_from_cmd_line(self):
        __main__.cmd()

    def it_should_not_send_a_coloured_reporter_to_main(self):
        self.mock_main.assert_called_once_with(os.getcwd(), [Shuffler(), cli.DotsReporter(sys.stdout), cli.SummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)], True)

    def cleanup_import(self):
        builtins.__import__ = self.real_import


class WhenStdOutIsAPipe(MainSharedContext):
    def establish_that_stdout_is_a_pipe(self):
        sys.stdout.isatty = lambda: False

    def because_we_run_from_cmd_line(self):
        __main__.cmd()

    def it_should_not_send_a_coloured_reporter_to_main(self):
        self.mock_main.assert_called_once_with(os.getcwd(), [Shuffler(), cli.DotsReporter(sys.stdout), cli.SummarisingCapturingReporter(sys.stdout), cli.TimedReporter(sys.stdout)], True)


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
    def __init__(self, not_stream):
        self.not_stream = not_stream
    def __eq__(self, other):
        return type(other) == cli.StdOutCapturingReporter and other.stream != self.not_stream
