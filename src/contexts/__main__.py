import argparse
import inspect
import itertools
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
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (Default: current directory)")

    all_plugins = make_plugin_instances()

    call_plugins_to_set_up_parser(all_plugins, parser)
    args = parse_args(parser)

    active_plugins = initialise_plugins(all_plugins, args)

    inject_plugins_into_one_another(active_plugins)

    main(os.path.realpath(args.path), active_plugins)


def make_plugin_instances():
    builder = PluginListBuilder()
    for cls in [ExitCodeReporter,
                Shuffler, Importer,
                AssertionRewritingImporter,
                DecoratorBasedIdentifier,
                NameBasedIdentifier,
                teamcity.TeamCityReporter,
                cli.DotsReporter,
                cli.VerboseReporter,
                cli.StdOutCapturingReporter,
                cli.Colouriser, cli.UnColouriser,
                cli.FailuresOnlyMaster, cli.FailuresOnlyBefore, cli.FailuresOnlyAfter,
                cli.FinalCountsReporter, cli.TimedReporter]:
        builder.add(cls)
    return [activate_plugin(p) for p in builder.to_list()]


def call_plugins_to_set_up_parser(plugin_list, parser):
    for plug in plugin_list:
        if hasattr(plug, "setup_parser"):
            plug.setup_parser(parser)


def initialise_plugins(plugin_list, args):
    new_list = []
    for plug in plugin_list:
        include = plug.initialise(args, os.environ)
        if include:
            new_list.append(plug)
    return new_list


def inject_plugins_into_one_another(active_plugins):
    for plug in active_plugins:
        if hasattr(plug, 'request_plugins'):
            gen = plug.request_plugins()
            if gen is None:
                continue
            requested = next(gen)
            to_send = {}
            for requested_class, active_instance in itertools.product(requested, active_plugins):
                if isinstance(active_instance, requested_class):
                    to_send[requested_class] = active_instance
            try:
                gen.send(to_send)
            except StopIteration:  # should happen every time
                pass


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

def parse_args(parser):
    return parser.parse_args(sys.argv[1:])


if __name__ == "__main__":
	cmd()
