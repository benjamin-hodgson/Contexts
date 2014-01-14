import re
import traceback
from . import Plugin
from ..tools import NO_EXAMPLE


class StreamReporter(Plugin):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def _print(self, *args, sep=' ', end='\n', flush=True):
        print(*args, sep=sep, end=end, file=self.stream, flush=flush)

    def __eq__(self, other):
        return type(self) == type(other) and self.stream == other.stream


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
