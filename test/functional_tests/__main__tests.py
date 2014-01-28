import builtins
import os
import sys
from io import StringIO
from unittest import mock
import colorama
import contexts
from contexts import __main__
from contexts.plugins import cli
from contexts.plugins.shuffling import Shuffler
from contexts.plugins.importing import Importer
from contexts.plugins.shared import ExitCodeReporter
from contexts.plugins.teamcity import TeamCityReporter
from contexts.plugins.assertion_rewriting import AssertionRewritingImporter
from contexts.plugins.name_based_identifier import NameBasedIdentifier
from contexts.plugins.decorators import DecoratorBasedIdentifier


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


class WhenRunningFromCommandLineWithNoArguments(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.ColouringDecorator(cli.StdOutCapturingReporter))(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_the_default_plugins(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenSpecifyingAPath(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.ColouringDecorator(cli.StdOutCapturingReporter))(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        self.path = os.path.join(os.getcwd(),'made','up','path')
        sys.argv = ['run-contexts', self.path]

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_the_path(self):
        self.mock_main.assert_called_once_with(self.path, self.expected_plugins)


class WhenUsingTheVerboseFlag(MainSharedContext):
    @classmethod
    def examples_of_ways_to_use_the_verbose_flag(cls):
        yield '--verbose'
        yield '-v'

    def establish_arguments(self, flag):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.ColouringDecorator(cli.StdOutCapturingReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', flag]

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_verbose_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesColour(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.StdOutCapturingReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', '--no-colour']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_coloured_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenDisablingColourInVerboseMode(MainSharedContext):
    @classmethod
    def examples(self):
        yield ['--verbose', '--no-colour']
        yield ['-v', '--no-colour']

    def establish_arguments(self, args):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.StdOutCapturingReporter(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts'] + args

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_coloured_verbose_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesStdOutCapturing(MainSharedContext):
    @classmethod
    def examples(self):
        yield '--no-capture'
        yield '-s'

    def establish_arguments(self, arg):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.ColouringDecorator(cli.VerboseReporter))(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', arg]

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_capturing_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesCapturingInVerboseMode(MainSharedContext):
    @classmethod
    def examples_of_flag_combinations(self):
        yield ['--verbose', '--no-capture']
        yield ['-v', '--no-capture']
        yield ['--verbose', '-s']
        yield ['-v', '-s']
        yield ['-vs']

    def establish_arguments(self, args):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.ColouringDecorator(cli.VerboseReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts'] + args

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_capturing_verbose_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesColourAndCapturing(MainSharedContext):
    @classmethod
    def examples_of_flag_combinations(self):
        yield ['--no-capture', '--no-colour']
        yield ['-s', '--no-colour']

    def establish_arguments(self, args):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.VerboseReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts'] + args

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_coloured_non_capturing_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesColourAndCapturingInVerboseMode(MainSharedContext):
    @classmethod
    def examples_of_flag_combinations(self):
        yield ['--verbose', '--no-colour', '--no-capture']
        yield ['-v', '--no-colour', '--no-capture']
        yield ['--verbose', '--no-colour', '-s']
        yield ['-v', '--no-colour', '--no-capture']
        yield ['-vs', '--no-colour']

    def establish_arguments(self, args):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.VerboseReporter(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts'] + args

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_non_coloured_non_capturing_verbose_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenRunningInQuietMode(MainSharedContext):
    @classmethod
    def examples_of_ways_to_use_the_quiet_flag(self):
        yield '-q'
        yield '--quiet'

    def establish_arguments(self, flag):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            QuietReporterResemblance(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', flag]

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_quiet_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenDisablingAssertionRewriting(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            Importer(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.ColouringDecorator(cli.StdOutCapturingReporter))(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', '--no-assert']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_tell_main_to_disable_assertion_rewriting(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenRunningOnTheCmdLineInTeamcityMode(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            TeamCityReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', '--teamcity']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_teamcity_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenRunningInTeamcity(MainSharedContext):
    def establish_that_teamcity_is_in_the_environment_variables(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            Shuffler(),
            TeamCityReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        os.environ["TEAMCITY_VERSION"] = "7.0"
        sys.argv = ['run-contexts']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_with_a_teamcity_reporter(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenUserDisablesShuffling(MainSharedContext):
    def establish_arguments(self):
        self.expected_plugins = [
            AssertionRewritingImporter(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.ColouringDecorator(cli.StdOutCapturingReporter))(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ]
        sys.argv = ['run-contexts', '--no-random']

    def because_we_call_cmd(self):
        __main__.cmd()

    def it_should_call_main_without_a_shuffler(self):
        self.mock_main.assert_called_once_with(os.getcwd(), self.expected_plugins)


class WhenArgumentsSpecifyMutuallyExclusiveOptions(MainSharedContext):
    @classmethod
    def examples_of_flag_combinations(cls):
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
        self.mock_main.assert_called_once_with(os.getcwd(), [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.StdOutCapturingReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ])

    def cleanup_import(self):
        builtins.__import__ = self.real_import


class WhenStdOutIsAPipe(MainSharedContext):
    def establish_that_stdout_is_a_pipe(self):
        sys.stdout.isatty = lambda: False

    def because_we_run_from_cmd_line(self):
        __main__.cmd()

    def it_should_not_send_a_coloured_reporter_to_main(self):
        self.mock_main.assert_called_once_with(os.getcwd(), [
            AssertionRewritingImporter(),
            Shuffler(),
            cli.DotsReporter(sys.stdout),
            cli.FailureOnlyDecorator(cli.StdOutCapturingReporter)(sys.stdout),
            cli.FinalCountsReporter(sys.stdout),
            cli.TimedReporter(sys.stdout),
            DecoratorBasedIdentifier(),
            NameBasedIdentifier(),
            ExitCodeReporter()
        ])


###########################################################
# Test helper methods
###########################################################

class QuietReporterResemblance(object):
    """
    Compares equal to quiet reporters
    """
    def __init__(self, not_stream):
        self.not_stream = not_stream
    def __eq__(self, other):
        return type(other) == cli.StdOutCapturingReporter and other.stream != self.not_stream
