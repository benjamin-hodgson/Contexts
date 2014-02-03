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
    builder.add(cli.DotsReporter)
    builder.add(teamcity.TeamCityReporter)
    builder.add(cli.VerboseReporter)
    builder.add(cli.StdOutCapturingReporter)
    builder.add(cli.Colouriser)
    builder.add(cli.UnColouriser)
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

    new_list.extend(activate_plugin(cls) for cls in create_reporting_plugins(args))
    main(os.path.realpath(args.path), new_list)


def setup_parser(parser):
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (Default: current directory)")
    return parser


def create_reporting_plugins(args):
    if args.teamcity or args.verbosity == 'quiet':
        return []
    return [
        cli.FinalCountsReporter,
        cli.TimedReporter
    ]


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
