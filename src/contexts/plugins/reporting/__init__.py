import re
import sys
import traceback
from ...plugin_interface import PluginInterface, NO_EXAMPLE


class StreamReporter(PluginInterface):
    def __init__(self, stream=sys.stdout):
        self.stream = stream
    def _print(self, string, end='\n'):
        print(string, end=end, file=self.stream, flush=True)
    def __eq__(self, other):
        return type(self) == type(other) and self.stream == other.stream


class ExitCodeReporter(object):
    @classmethod
    def locate(cls):
        from .cli import FailuresOnlyBefore
        return (None, FailuresOnlyBefore)
    def initialise(self, args, env):
        return True

    def __init__(self):
        self.exit_code = 0
    def get_exit_code(self):
        return self.exit_code
    def assertion_failed(self, name, exception):
        self.exit_code = 1
    def assertion_errored(self, name, exception):
        self.exit_code = 1
    def context_errored(self, name, example, exception):
        self.exit_code = 1
    def test_class_errored(self, cls, exception):
        self.exit_code = 1
    def unexpected_error(self, exception):
        self.exit_code = 1
    def __eq__(self, other):
        return type(self) == type(other)


def make_readable(string):
    regex = re.compile(r'(_|\.|{}|{}|{})'.format(
        r'(?<=[^A-Z])(?=[A-Z])',
        r'(?<=[A-Z])(?=[A-Z][a-z])',
        r'(?<=[A-Za-z])(?=[^A-Za-z])'
    ))
    words = regex.sub(' ', string).split(' ')

    cased_words = [words[0]]
    for word in words[1:]:
        should_lowerise = (not word.isupper()) or (len(word) == 1)
        cased_word = word.lower() if should_lowerise else word
        cased_words.append(cased_word)
    return ' '.join(cased_words)


def context_name(name, example):
    if example is NO_EXAMPLE:
        return make_readable(name)
    else:
        return make_readable(name) + " -> " + str(example)


def format_exception(exception):
    ret = traceback.format_exception(type(exception), exception, exception.__traceback__)
    return ''.join(ret).strip().split('\n')
