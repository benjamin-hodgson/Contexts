import argparse
import inspect
import itertools
import os
import sys
import pkg_resources
from . import main
from .plugin_discovery import PluginListBuilder


def cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
        action='store',
        nargs='?',
        default=os.getcwd(),
        help="Path to the test file or directory to run. (Default: current directory)")

    plugin_activator = PluginActivator()
    plugin_activator.load_plugins()
    plugin_activator.setup_parser(parser)

    args = parser.parse_args(sys.argv[1:])

    plugin_activator.initialise_plugins(args)
    plugin_activator.cross_pollinate()

    main(os.path.realpath(args.path), plugin_activator.to_list())


class PluginActivator(object):
    def load_plugins(self):
        builder = PluginListBuilder()
        for entry_point in pkg_resources.iter_entry_points('contexts.plugins'):
            cls = entry_point.load()
            builder.add(cls)

        self.plugins = [self.activate_plugin(p) for p in builder.to_list()]

    def setup_parser(self, parser):
        for plug in self.plugins:
            if hasattr(plug, "setup_parser"):
                plug.setup_parser(parser)

    def initialise_plugins(self, args):
        new_list = []
        for plug in self.plugins:
            include = plug.initialise(args, os.environ)
            if include:
                new_list.append(plug)
        self.plugins = new_list

    def cross_pollinate(self):
        for plug in self.plugins:
            if hasattr(plug, 'request_plugins'):
                gen = plug.request_plugins()
                if gen is None:
                    continue
                requested = next(gen)
                to_send = {}
                for requested_class, active_instance in itertools.product(requested, self.plugins):
                    if isinstance(active_instance, requested_class):
                        to_send[requested_class] = active_instance
                try:
                    gen.send(to_send)
                except StopIteration:  # should happen every time
                    pass

    def to_list(self):
        return self.plugins


    def activate_plugin(self, cls):
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
