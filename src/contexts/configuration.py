import random


class Configuration(object):
    def __init__(self, shuffle=False, rewriting=False, plugins=()):
        self.rewriting = rewriting
        self.plugins = []
        self.plugins.extend(plugins)

    def __getattr__(self, name):
        return PluginProxy(self.plugins, name)

    def __eq__(self, other):
        print(self.plugins, other.plugins)
        return (self.plugins == other.plugins
            and self.rewriting == other.rewriting)


class PluginProxy(object):
    def __init__(self, plugins, name):
        self.plugins = plugins
        self.name = name

    def __call__(self, *args, **kwargs):
        for plugin in self.plugins:
            getattr(plugin, self.name)(*args, **kwargs)


class NullConfiguration(object):
    def __init__(self):
        self.rewriting = False
    def process_module_list(self, l):
        pass
    def process_class_list(self, l):
        pass
    def process_assertion_list(self, l):
        pass
    def shuffle_list(self, l):
        pass


class Shuffler(object):
    def process_module_list(self, l):
        self.shuffle_list(l)
    def process_class_list(self, l):
        self.shuffle_list(l)
    def process_assertion_list(self, l):
        self.shuffle_list(l)
    def shuffle_list(self, l):
        random.shuffle(l)

    def __eq__(self, other):
        return isinstance(other, Shuffler)
