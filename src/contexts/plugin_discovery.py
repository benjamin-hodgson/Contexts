import argparse
import inspect
import itertools
import os
import sys
import pkg_resources


def load_plugins():
    plugin_loader = PluginLoader()

    parser = argparse.ArgumentParser()

    plugin_loader.load_plugins()
    plugin_loader.setup_parser(parser)

    args = parser.parse_args(sys.argv[1:])

    plugin_loader.initialise_plugins(args)
    plugin_loader.cross_pollinate()

    return plugin_loader.to_list()



class PluginLoader(object):
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

    # this function should go
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


class PluginListBuilder(object):
    def __init__(self):
        self.graph = Graph()

    def add(self, cls):
        left, right = get_location(cls)
        self.graph.add_node(cls)
        if right is not None:
            self.graph.add_edge(cls, right)
        if left is not None:
            self.graph.add_edge(left, cls)

    def to_list(self):
        return self.graph.topological_sort()


def get_location(cls):
    if hasattr(cls, 'locate'):
        location = cls.locate()
        if location is None:
            return (None, None)
        else:
            return location
    else:
        return (None, None)


class Graph(object):
    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        if node in self.nodes and self.nodes[node]['added']:
            raise ValueError('Node has already been added')

        self.create_if_necessary(node)
        self.nodes[node]['added'] = True

    def add_edge(self, tail, head):
        self.create_if_necessary(tail)
        self.create_if_necessary(head)
        self.nodes[tail]['edges_to'].add(head)

    def topological_sort(self):
        sorter = TopologicalSorter(self)
        return sorter.sort()

    def create_if_necessary(self, node):
        if node not in self.nodes:
            self.nodes[node] = {'edges_to':set(), 'added':False}


class TopologicalSorter(object):
    # created this class because we don't want to mutate the graph itself during the topological sorting algorithm
    def __init__(self, graph):
        self.nodes = {}
        for key, dct in graph.nodes.items():
            self.nodes[key] = {'edges_to':dct['edges_to'], 'temp_mark':False, 'perm_mark':not dct['added']}
        self.output = []

    def sort(self):
        for node in self.nodes:
            self.visit(node)
        self.output.reverse()
        return self.output

    def visit(self, node):
        node_data = self.nodes[node]
        if node_data['perm_mark']:
            return
        if node_data['temp_mark']:
            raise ValueError('Graph has cycles')

        node_data['temp_mark'] = True

        for m in node_data['edges_to']:
            self.visit(m)

        self.output.append(node)
        node_data['perm_mark'] = True


