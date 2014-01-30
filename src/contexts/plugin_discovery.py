class PluginListBuilder(object):
    # Refactoring to-do: separate out the graph-related logic
    def __init__(self):
        self._plugins = {}
        self._output = []

    def add(self, cls):
        left, right = get_location(cls)

        if cls in self._plugins and self._plugins[cls]['perm_mark'] is False:
            raise ValueError('Plugin has already been added')

        self.create_entry(cls)
        self._plugins[cls]['perm_mark'] = False

        if right is not None:
            self.create_entry(right)
            self._plugins[cls]['left_of'].add(right)

        if left is not None:
            self.create_entry(left)
            self._plugins[left]['left_of'].add(cls)

    def to_list(self):
        for cls in self._plugins:
            self.visit(cls)
        self._output.reverse()
        return self._output

    def create_entry(self, cls):
        if cls not in self._plugins:
            self._plugins[cls] = {'left_of':set(), 'temp_mark':False, 'perm_mark':True}

    def visit(self, cls):
        dct = self._plugins[cls]

        if dct['perm_mark']:
            return
        if dct['temp_mark']:
            raise ValueError('Graph has cycles')

        dct['temp_mark'] = True
        for class_further_right in dct['left_of']:
            self.visit(class_further_right)

        self._output.append(cls)
        dct['perm_mark'] = True


def get_location(cls):
    if hasattr(cls, 'locate'):
        location = cls.locate()
        if location is None:
            return (None, None)
        else:
            return location
    else:
        return (None, None)

