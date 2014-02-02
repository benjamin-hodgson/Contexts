import argparse
import inspect
import os
import sys
from . import main
from .plugin_discovery import PluginListBuilder
from .plugins import cli, teamcity
from .plugins.shared import ExitCodeReporter
from .plugins.shuffling import Shuffler
from .plugins.importing import Importer
from .plugins.assertion_rewriting import AssertionRewritingImporter
from contexts.plugins.name_based_identifier import NameBasedIdentifier
from contexts.plugins.decorators import DecoratorBasedIdentifier


def cmd():
    builder = PluginListBuilder()
    builder.add(ExitCodeReporter)
    builder.add(Shuffler)
    builder.add(Importer)
    builder.add(AssertionRewritingImporter)
    builder.add(DecoratorBasedIdentifier)
    builder.add(NameBasedIdentifier)
    plugin_list = [activate_plugin(p) for p in builder.to_list()]

    parser = argparse.ArgumentParser()

    for plug in plugin_list:
        if hasattr(plug, "setup_parser"):
            plug.setup_parser(parser)

    setup_parser(parser)

    args = parser.parse_args(sys.argv[1:])

    if "TEAMCITY_VERSION" in os.environ:
        args.teamcity = True

    if not sys.stdout.isatty():
        args.colour = False

    if args.colour:
        try:
            import colorama
        except ImportError:
            args.colour = False
        else:
            colorama.init()

    new_list = []
    for plug in plugin_list:
        include = plug.initialise(args)
        if include:
            new_list.append(plug)

    new_list.extend(create_plugins(args))
    main(os.path.realpath(args.path), new_list)


def setup_parser(parser):
    parser.add_argument('-s', '--no-capture',
        action='store_false',
        dest='capture',
        default=True,
        help="Disable capturing of stdout during tests.")
    parser.add_argument('--teamcity',
        action='store_true',
        dest='teamcity',
        default=False,
        help="Enable teamcity test reporting.")
    parser.add_argument('--no-colour',
        action='store_false',
        dest='colour',
        default=True,
        help='Disable coloured output.')
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (default current directory)")

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

    return parser


def create_plugins(args):
    plugin_class_list = []

    plugin_class_list.extend(create_reporting_plugins(args))

    return [activate_plugin(cls) for cls in plugin_class_list]

def create_reporting_plugins(args):
    if args.teamcity:
        return [teamcity.TeamCityReporter]

    if args.verbosity == 'quiet':
        return [cli.QuietReporter]

    inner_plugin_cls = get_inner_plugin(args)
    maybe_coloured_cls = apply_colouring(args, inner_plugin_cls)
    maybe_muted_cls = apply_success_muting(args, maybe_coloured_cls)

    plugin_list = [
        maybe_muted_cls,
        cli.FinalCountsReporter,
        cli.TimedReporter
    ]

    if args.verbosity == 'normal':
        plugin_list.insert(0, cli.DotsReporter)

    return plugin_list

def get_inner_plugin(args):
    if args.capture:
        return cli.StdOutCapturingReporter
    return cli.VerboseReporter

def apply_colouring(args, inner_plugin_cls):
    if args.colour:
        return cli.ColouringDecorator(inner_plugin_cls)
    return inner_plugin_cls

def apply_success_muting(args, maybe_coloured_cls):
    if args.verbosity == 'normal':
        return cli.FailureOnlyDecorator(maybe_coloured_cls)
    return maybe_coloured_cls


def activate_plugin(cls):
    try:
        sig = inspect.signature(cls)
    except ValueError:
        # working around a bug in inspect.signature :(
        # http://bugs.python.org/issue20308
        # hopefully it'll be backported to a future version of 3.3
        # so I can take this out
        return cls()

    if sig.parameters:
        return cls(sys.stdout)

    return cls()


if __name__ == "__main__":
	cmd()
