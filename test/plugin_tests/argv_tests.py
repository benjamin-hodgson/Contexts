import sys

from contexts.plugins.argv_forwarder import ArgvForwarder

from .tools import ExceptionThrowingArgumentParser


class WhenInitialisingArgvForwarderWithNoArgvArgument:
    def given_plugin_and_no_command_line_args(self):
        self.plugin = ArgvForwarder()
        self.parser = ExceptionThrowingArgumentParser()
        self.args = []

    def when_the_plugin_is_initialised(self):
        self.plugin.setup_parser(self.parser)
        namespace = self.parser.parse_args(self.args)
        self.result = self.plugin.initialise(namespace, {})

    def it_should_not_be_added_to_the_list(self):
        assert not self.result


class WhenInitialisingArgvForwarderWithAnArgvArgument:
    def given_plugin_and_command_line_args(self):
        self.plugin = ArgvForwarder()
        self.parser = ExceptionThrowingArgumentParser()
        self.args = ["--argv", '-xy -z 5 --switch --arg 5']

    def when_the_plugin_is_initialised(self):
        self.plugin.setup_parser(self.parser)
        namespace = self.parser.parse_args(self.args)
        self.result = self.plugin.initialise(namespace, {})

    def it_should_be_added_to_the_list(self):
        assert self.result


class WhenSupplyingArgvAndTestRunStarts:
    def given_initialised_plugin(self):
        self.old_sys_dot_argv = sys.argv.copy()

        self.plugin = ArgvForwarder()
        self.parser = ExceptionThrowingArgumentParser()
        self.args = ["--argv", '-xy -z 5 --switch --arg 5']

        self.plugin.setup_parser(self.parser)
        namespace = self.parser.parse_args(self.args)
        self.plugin.initialise(namespace, {})

    def when_test_run_starts(self):
        self.plugin.test_run_started()

    def it_should_override_sys_dot_argv(self):
        assert sys.argv[1:] == ['-xy', '-z', '5', '--switch', '--arg', '5']

    def cleanup_sys_dot_argv(self):
        sys.argv = self.old_sys_dot_argv


class WhenSupplyingArgvAndTestRunEnds:
    def given_test_run_has_started(self):
        self.old_sys_dot_argv = sys.argv.copy()

        self.plugin = ArgvForwarder()
        self.parser = ExceptionThrowingArgumentParser()
        self.args = ["--argv", '-xy -z 5 --switch --arg 5']

        self.plugin.setup_parser(self.parser)
        namespace = self.parser.parse_args(self.args)
        self.plugin.initialise(namespace, {})
        self.plugin.test_run_started()

    def when_test_run_starts(self):
        self.plugin.test_run_ended()

    def it_should_reset_sys_dot_argv(self):
        assert sys.argv == self.old_sys_dot_argv
