import argparse
import datetime
import sys
from io import StringIO
from . import StreamReporter, context_name, format_exception, make_readable


class DotsReporter(StreamReporter):
    @classmethod
    def locate(cls):
        return (None, VerboseReporter)

    def initialise(self, args, env):
        return args.verbosity == 'normal'

    def assertion_passed(self, *args, **kwargs):
        self.dot()

    def assertion_failed(self, *args, **kwargs):
        self.F()

    def assertion_errored(self, *args, **kwargs):
        self.E()

    def context_errored(self, *args, **kwargs):
        self.E()

    def test_class_errored(self, *args, **kwargs):
        self.E()

    def unexpected_error(self, *args, **kwargs):
        self.E()

    def test_run_ended(self):
        self._print('')

    def dot(self):
        self._print('.', end='')

    def F(self):
        self._print('F', end='')

    def E(self):
        self._print('E', end='')


class VerboseReporter(StreamReporter):
    dashes = '-' * 70

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

    def initialise(self, args, env):
        return args.verbosity != "quiet"

    def context_started(self, cls, example):
        self._print(context_name(cls.__name__, example))

    def context_errored(self, name, example, exception):
        for line in format_exception(exception):
            self._print('  ' + line)

    def test_class_errored(self, cls, exception):
        for line in format_exception(exception):
            self._print(line)

    def assertion_passed(self, func):
        self._print('  PASS: ' + make_readable(func.__name__))

    def assertion_failed(self, func, exception):
        self._print('  FAIL: ' + make_readable(func.__name__))
        for line in format_exception(exception):
            self._print('    ' + line)

    def assertion_errored(self, func, exception):
        self._print('  ERROR: ' + make_readable(func.__name__))
        for line in format_exception(exception):
            self._print('    ' + line)

    def unexpected_error(self, exception):
        for line in format_exception(exception):
            self._print(line)


class FinalCountsReporter(StreamReporter):
    dashes = '-' * 70

    @classmethod
    def locate(cls):
        return (VerboseReporter, None)

    def initialise(self, args, env):
        return args.verbosity != 'quiet'

    def __init__(self, stream=sys.stdout):
        super().__init__(stream)
        self.context_count = 0
        self.assertion_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.failed = False

    def context_started(self, name, example):
        self.context_count += 1

    def context_errored(self, name, example, exception):
        self.error_count += 1
        self.failed = True

    def assertion_started(self, func):
        self.assertion_count += 1

    def assertion_failed(self, func, exception):
        self.failure_count += 1
        self.failed = True

    def assertion_errored(self, func, exception):
        self.error_count += 1
        self.failed = True

    def unexpected_error(self, exception):
        self.error_count += 1
        self.failed = True

    def test_class_errored(self, cls, exception):
        self.error_count += 1
        self.failed = True

    def test_run_ended(self):
        self.summarise()

    def summarise(self):
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


class StdOutCapturingReporter(StreamReporter):
    @classmethod
    def locate(cls):
        return (VerboseReporter, FinalCountsReporter)

    def setup_parser(self, parser):
        parser.add_argument('-s', '--no-capture',
                            action='store_false',
                            dest='capture',
                            default=True,
                            help="Disable capturing of stdout during tests.")

    def initialise(self, args, env):
        self.quiet = args.verbosity == "quiet"
        return args.capture and not (args.teamcity or 'TEAMCITY_VERSION' in env)

    def centred_dashes(self, string, indentation):
        num = str(70 - indentation)
        return ("{:-^" + num + "}").format(string)

    def context_started(self, name, example):
        self.real_stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer

    def context_ended(self, name, example):
        sys.stdout = self.real_stdout

    def context_errored(self, name, example, exception):
        sys.stdout = self.real_stdout
        self.output_buffer(2)

    def assertion_failed(self, func, exception):
        self.output_buffer(4)

    def assertion_errored(self, func, exception):
        self.output_buffer(4)

    def output_buffer(self, indentation):
        if self.buffer.getvalue() and not self.quiet:
            lines = [self.centred_dashes(" >> begin captured stdout << ", indentation)]
            lines.extend(self.buffer.getvalue().strip().split('\n'))
            lines.append(self.centred_dashes(" >> end captured stdout << ", indentation))
            for line in lines:
                self._print((' ' * indentation) + line)


class TimedReporter(StreamReporter):
    @classmethod
    def locate(self):
        return (FinalCountsReporter, None)

    def initialise(self, args, env):
        return not args.verbosity == 'quiet'

    def test_run_started(self):
        self.start_time = datetime.datetime.now()

    def test_run_ended(self):
        self.end_time = datetime.datetime.now()
        self.print_time()

    def print_time(self):
        total_secs = (self.end_time - self.start_time).total_seconds()
        rounded = round(total_secs, 1)
        self._print("({} seconds)".format(rounded))


class Colouriser(StreamReporter):
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

    def initialise(self, args, env):
        if not sys.stdout.isatty():
            return False
        if args.colour:
            global colorama
            try:
                import colorama  # noqa
            except ImportError:
                return False
            return True

    def context_errored(self, name, example, exception):
        self.stream.write(colorama.Fore.RED)  # noqa

    def assertion_passed(self, func):
        self.stream.write(colorama.Fore.GREEN)  # noqa

    def assertion_failed(self, func, exception):
        self.stream.write(colorama.Fore.RED)  # noqa

    def assertion_errored(self, func, exception):
        self.stream.write(colorama.Fore.RED)  # noqa

    def test_class_errored(self, cls, exception):
        self.stream.write(colorama.Fore.RED)  # noqa

    def unexpected_error(self, exception):
        self.stream.write(colorama.Fore.RED)  # noqa


class UnColouriser(StreamReporter):
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

    def initialise(self, args, env):
        if not sys.stdout.isatty():
            return False
        if args.colour:
            global colorama
            try:
                import colorama  # noqa
            except ImportError:
                return False
            return True

    def context_errored(self, name, example, exception):
        self.stream.write(colorama.Fore.RESET)  # noqa

    def assertion_passed(self, func):
        self.stream.write(colorama.Fore.RESET)  # noqa

    def assertion_failed(self, func, exception):
        self.stream.write(colorama.Fore.RESET)  # noqa

    def assertion_errored(self, func, exception):
        self.stream.write(colorama.Fore.RESET)  # noqa

    def test_class_errored(self, cls, exception):
        self.stream.write(colorama.Fore.RESET)  # noqa

    def unexpected_error(self, exception):
        self.stream.write(colorama.Fore.RESET)  # noqa


# these three are kinda hideous
class FailuresOnlyMaster(StreamReporter):
    def __init__(self, stream):
        super().__init__(stream)
        self.plugins = []
        self.final_report = StringIO()
        self.fake_stream = StringIO()

    @classmethod
    def locate(cls):
        return (None, FinalCountsReporter)

    def initialise(self, args, env):
        return args.verbosity == 'normal'

    def request_plugins(self):
        returned_plugins = yield [Colouriser, VerboseReporter, StdOutCapturingReporter, UnColouriser]
        self.plugins = returned_plugins.values()

    def set_streams(self, stream):
        self.fake_stream = stream
        for plugin in self.plugins:
            plugin.stream = stream


class FailuresOnlyBefore(object):
    dashes = '-' * 70

    @classmethod
    def locate(cls):
        return (DotsReporter, Colouriser)

    def initialise(self, args, env):
        return args.verbosity == 'normal'

    def request_plugins(self):
        returned_plugins = yield [FailuresOnlyMaster]
        self.master = returned_plugins[FailuresOnlyMaster]

    def context_started(self, name, example):
        self.master.set_streams(StringIO())
        self.master.current_context_failed = False

    def assertion_passed(self, func):
        return True

    def assertion_failed(self, func, exception):
        self.master.current_context_failed = True

    def assertion_errored(self, func, exception):
        self.master.current_context_failed = True

    def test_class_errored(self, cls, exception):
        self.unexpected_error(exception)

    def unexpected_error(self, exception):
        # write the error directly to the report
        self.master.orig_stream = self.master.fake_stream
        self.master.set_streams(self.master.final_report)

    def test_run_ended(self):
        output = self.master.final_report.getvalue()
        if output:
            self.master.stream.write(self.dashes + '\n')
            self.master.stream.write(output.strip() + '\n')

    def __eq__(self, other):
        return type(self) == type(other)


class FailuresOnlyAfter(object):
    @classmethod
    def locate(cls):
        return (UnColouriser, None)

    def initialise(self, args, env):
        return args.verbosity == 'normal'

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
