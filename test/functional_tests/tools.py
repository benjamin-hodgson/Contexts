import contexts
from contexts.plugins.test_target_suppliers import ObjectSupplier


class UnorderedList(object):
    def __init__(self, l):
        self._list = l

    def __eq__(self, other):
        if len(other) != len(self._list):
            return False
        for member in other:
            if member not in self._list:
                return False
        return True


def run_object(to_run, plugins):
    extra_plug = ObjectSupplier(to_run)
    plugins.insert(0, extra_plug)
    return contexts.run_with_plugins(plugins)
