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
        self.output = []

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


