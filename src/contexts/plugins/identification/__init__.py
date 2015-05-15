import os.path
import re
from contexts.plugin_interface import TEST_FOLDER, TEST_FILE, CONTEXT, EXAMPLES, SETUP, ACTION, ASSERTION, TEARDOWN
from contexts import errors
from .. import cleverly_get_words


folder_re = re.compile(r"[Ss]pec|[Tt]est")
file_re = re.compile(r"([Ss]pec|[Tt]est).*?\.py$")
class_re = re.compile(r"[Ss]pec|[Ww]hen")

example_words = frozenset(("example", "examples", "data"))
setup_words = frozenset(("establish", "context", "given"))
action_words = frozenset(("because", "when", "since", "after"))
assertion_words = frozenset(("should", "it", "must", "will", "then"))
cleanup_words = frozenset(("cleanup",))


class NameBasedIdentifier(object):
    def initialise(self, args, env):
        return True

    def identify_folder(self, folder):
        folder_name = os.path.basename(folder)
        if folder_re.search(folder_name):
            return TEST_FOLDER

    def identify_file(self, file):
        file_name = os.path.basename(file)
        if file_re.search(file_name):
            return TEST_FILE

    def identify_class(self, cls):
        if class_re.search(cls.__name__):
            return CONTEXT

    def identify_method(self, method):
        d = {
            example_words: EXAMPLES,
            setup_words: SETUP,
            action_words: ACTION,
            assertion_words: ASSERTION,
            cleanup_words: TEARDOWN
        }
        name = method.__name__

        for word in get_lowercase_words(name):
            for keywords in d:
                if word in keywords:
                    assert_not_ambiguous(name, keywords)
                    return d[keywords]

    def __eq__(self, other):
        return type(self) == type(other)


def assert_not_ambiguous(name, keywords):
    all_keyword_sets = {example_words, setup_words, action_words, assertion_words, cleanup_words}
    all_keyword_sets.remove(keywords)

    for word in get_lowercase_words(name):
        if any(word in s for s in all_keyword_sets):
            msg = """The method {} is ambiguously named.
You can override this check by explicitly marking your
method using one of the decorators in the 'contexts' module:
http://contexts.readthedocs.org/en/latest/guide.html#overriding-name-based-usage
""".format(name)
            raise errors.MethodNamingError(msg)


def get_lowercase_words(string):
    return (s.lower() for s in cleverly_get_words(string))
