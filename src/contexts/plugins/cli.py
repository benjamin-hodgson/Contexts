import argparse
import datetime
import sys
from io import StringIO
from . import shared
from .name_based_identifier import NameBasedIdentifier


class DotsReporter(shared.StreamReporter):
    @classmethod
    def locate(cls):
        return (NameBasedIdentifier, VerboseReporter)
    def initialise(self, args):
        return args.verbosity == 'normal' and not args.teamcity

    def assertion_passed(self, *args, **kwargs):
        super().assertion_passed(*args, **kwargs)
        self._print('.', end='')

    def assertion_failed(self, *args, **kwargs):
        super().assertion_failed(*args, **kwargs)
        self._print('F', end='')

    def assertion_errored(self, *args, **kwargs):
        super().assertion_errored(*args, **kwargs)
        self._print('E', end='')

    def context_errored(self, *args, **kwargs):
        super().context_errored(*args, **kwargs)
        self._print('E', end='')

    def unexpected_error(self, *args, **kwargs):
        super().unexpected_error(*args, **kwargs)
        self._print('E', end='')


class VerboseReporter(shared.StreamReporter):
    dashes = '-' * 70

    @classmethod
    def locate(cls):
        return (NameBasedIdentifier, None)

    def setup_parser(self, parser):
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('-v', '--verbose',
            action='store_const',
            dest='verbosity',
            const='verbose',
            default='normal',
            help="Enable verbose progress reporting.")
        group.add_argument('-q', '--quiet',
            action='store_const',
            dest='verbosity',
            const='quiet',
            default='normal',
            help="Disable progress reporting.")

    def initialise(self, args):
        return args.verbosity != "quiet" and not args.teamcity

    def context_started(self, name, example):
        super().context_started(name, example)
        self._print(shared.context_name(name, example))

    def context_errored(self, name, example, exception):
        super().context_errored(name, example, exception)
        for line in shared.format_exception(exception):
            self._print('  ' + line)

    def assertion_passed(self, name):
        super().assertion_passed(name)
        self._print('  PASS: ' + shared.make_readable(name))

    def assertion_failed(self, name, exception):
        super().assertion_failed(name, exception)
        self._print('  FAIL: ' + shared.make_readable(name))
        for line in shared.format_exception(exception):
            self._print('    ' + line)

    def assertion_errored(self, name, exception):
        super().assertion_errored(name, exception)
        self._print('  ERROR: ' + shared.make_readable(name))
        for line in shared.format_exception(exception):
            self._print('    ' + line)

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        for line in shared.format_exception(exception):
            self._print(line)


class FinalCountsReporter(shared.StreamReporter):
    dashes = '-' * 70

    @classmethod
    def locate(cls):
        return (FailuresOnlyMaster, None)

    def initialise(self, args):
        return not args.teamcity and not args.verbosity == 'quiet'

    def __init__(self, stream=sys.stdout):
        super().__init__(stream)
        self.context_count = 0
        self.assertion_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.failed = False

    def context_started(self, name, example):
        super().context_started(name, example)
        self.context_count += 1

    def context_errored(self, name, example, exception):
        super().context_errored(name, example, exception)
        self.error_count += 1
        self.failed = True

    def assertion_started(self, name):
        super().assertion_started(name)
        self.assertion_count += 1

    def assertion_failed(self, name, exception):
        super().assertion_failed(name, exception)
        self.failure_count += 1
        self.failed = True

    def assertion_errored(self, name, exception):
        super().assertion_errored(name, exception)
        self.error_count += 1
        self.failed = True

    def unexpected_error(self, exception):
        super().unexpected_error(exception)
        self.error_count += 1
        self.failed = True

    def test_run_ended(self):
        super().test_run_ended()
        self.summarise()

    def summarise(self):
        self._print('')
        self._print(self.dashes)
        if self.failure_count or self.error_count:
            self._print('FAILED!')
            self._print(self.failure_numbers())
        else:
            self._print('PASSED!')
            self._print(self.success_numbers())

    def success_numbers(self):
        return "{}, {}".format(
            pluralise("context", self.context_count),
            pluralise("assertion", self.assertion_count))

    def failure_numbers(self):
        return "{}, {}: {} failed, {}".format(
            pluralise("context", self.context_count),
            pluralise("assertion", self.assertion_count),
            self.failure_count,
            pluralise("error", self.error_count))


class StdOutCapturingReporter(shared.StreamReporter):
    @classmethod
    def locate(cls):
        return (VerboseReporter, None)

    def setup_parser(self, parser):
        parser.add_argument('-s', '--no-capture',
            action='store_false',
            dest='capture',
            default=True,
            help="Disable capturing of stdout during tests.")

    def initialise(self, args):
        return args.capture and not args.teamcity and args.verbosity != "quiet"

    def centred_dashes(self, string, indentation):
        num = str(70 - indentation)
        return ("{:-^"+num+"}").format(string)

    def context_started(self, name, example):
        super().context_started(name, example)
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer

    def context_ended(self, name, example):
        super().context_ended(name, example)
        sys.stdout = self.real_stdout

    def context_errored(self, name, example, exception):
        super().context_errored(name, example, exception)
        sys.stdout = self.real_stdout
        self.output_buffer(2)

    def assertion_failed(self, name, exception):
        super().assertion_failed(name, exception)
        self.output_buffer(4)

    def assertion_errored(self, name, exception):
        super().assertion_errored(name, exception)
        self.output_buffer(4)

    def output_buffer(self, indentation):
        if self.buffer.getvalue():
            lines = [self.centred_dashes(" >> begin captured stdout << ", indentation)]
            lines.extend(self.buffer.getvalue().strip().split('\n'))
            lines.append(self.centred_dashes(" >> end captured stdout << ", indentation))
            for line in lines:
                self._print(' '*(indentation) + line)


class TimedReporter(shared.StreamReporter):
    @classmethod
    def locate(self):
        return (FinalCountsReporter, None)
    def initialise(self, args):
        return not args.teamcity and not args.verbosity == 'quiet'
    def test_run_started(self):
        super().test_run_started()
        self.start_time = datetime.datetime.now()

    def test_run_ended(self):
        super().test_run_ended()
        self.end_time = datetime.datetime.now()
        self.print_time()

    def print_time(self):
        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


class Colouriser(shared.StreamReporter):
    @classmethod
    def locate(cls):
        return (DotsReporter, VerboseReporter)

    def setup_parser(self, parser):
        try:
            parser.add_argument('--no-colour',
                action='store_false',
                dest='colour',
                default=True,
                help='Disable coloured output.')
        except argparse.ArgumentError:
            # just means the other one already did it
            pass

    def initialise(self, args):
        if args.colour:
            global colorama
            import colorama
        return args.colour and not args.teamcity and args.verbosity != 'quiet'

    def context_errored(self, name, example, exception):
        self.stream.write(colorama.Fore.RED)

    def assertion_passed(self, name):
        self.stream.write(colorama.Fore.GREEN)

    def assertion_failed(self, name, exception):
        self.stream.write(colorama.Fore.RED)

    def assertion_errored(self, name, exception):
        self.stream.write(colorama.Fore.RED)

    def unexpected_error(self, exception):
        self.stream.write(colorama.Fore.RED)


class UnColouriser(shared.StreamReporter):
    @classmethod
    def locate(cls):
        return (StdOutCapturingReporter, None)

    def setup_parser(self, parser):
        try:
            parser.add_argument('--no-colour',
                action='store_false',
                dest='colour',
                default=True,
                help='Disable coloured output.')
        except argparse.ArgumentError:
            # just means the other one already did it
            pass

    def initialise(self, args):
        if args.colour:
            global colorama
            import colorama
        return args.colour and not args.teamcity and args.verbosity != 'quiet'

    def context_errored(self, name, example, exception):
        self.stream.write(colorama.Fore.RESET)

    def assertion_passed(self, name):
        self.stream.write(colorama.Fore.RESET)

    def assertion_failed(self, name, exception):
        self.stream.write(colorama.Fore.RESET)

    def assertion_errored(self, name, exception):
        self.stream.write(colorama.Fore.RESET)

    def unexpected_error(self, exception):
        self.stream.write(colorama.Fore.RESET)


# these three are kinda hideous
class FailuresOnlyMaster(shared.StreamReporter):
    def __init__(self, stream):
        super().__init__(stream)
        self.plugins = []
        self.final_report = StringIO()

    @classmethod
    def locate(cls):
        return (FailuresOnlyAfter, None)

    def initialise(self, args):
        return args.verbosity == 'normal' and not args.teamcity

    def request_plugins(self):
        wanted_classes = [Colouriser, VerboseReporter, StdOutCapturingReporter, UnColouriser]
        returned_plugins = yield wanted_classes
        for cls in wanted_classes:
            if cls in returned_plugins:
                self.plugins.append(returned_plugins[cls])

    def set_streams(self, stream):
        self.fake_stream = stream
        for plugin in self.plugins:
            plugin.stream = stream



class FailuresOnlyBefore(object):
    dashes = '-' * 70

    @classmethod
    def locate(cls):
        return (DotsReporter, Colouriser)

    def initialise(self, args):
        return args.verbosity == 'normal' and not args.teamcity

    def request_plugins(self):
        returned_plugins = yield [FailuresOnlyMaster]
        self.master = returned_plugins[FailuresOnlyMaster]

    def context_started(self, name, example):
        self.master.set_streams(StringIO())
        self.master.current_context_failed = False
    def assertion_failed(self, name, exception):
        self.master.current_context_failed = True
    def assertion_errored(self, name, exception):
        self.master.current_context_failed = True

    def unexpected_error(self, exception):
        # write the error directly to the report
        self.master.orig_stream = self.master.fake_stream
        self.master.set_streams(self.master.final_report)

    def test_run_ended(self):
        output = self.master.final_report.getvalue()
        if output:
            self.master.stream.write('\n' + self.dashes + '\n')
            self.master.stream.write(output.strip())

    def __eq__(self, other):
        return type(self) == type(other)


class FailuresOnlyAfter(object):
    @classmethod
    def locate(cls):
        return (UnColouriser, None)

    def initialise(self, args):
        return args.verbosity == 'normal' and not args.teamcity

    def request_plugins(self):
        returned_plugins = yield [FailuresOnlyMaster]
        self.master = returned_plugins[FailuresOnlyMaster]

    def context_ended(self, name, example):
        if self.master.current_context_failed:
            self.master.final_report.write(self.master.fake_stream.getvalue())
        self.master.set_streams(StringIO())
    def context_errored(self, name, example, exception):
        self.master.final_report.write(self.master.fake_stream.getvalue())
        self.master.set_streams(StringIO())
    def unexpected_error(self, exception):
        self.master.set_streams(self.master.orig_stream)

    def __eq__(self, other):
        return type(self) == type(other)


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
