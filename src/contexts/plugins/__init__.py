class Plugin(object):
    """
    Interface for a plugin
    """
    def test_run_started(self):
        """Called at the beginning of a test run"""
    def test_run_ended(self):
        """Called at the end of a test run"""

    def suite_started(self, name):
        """Called at the start of a test module"""
    def suite_ended(self, name):
        """Called at the end of a test module"""

    def context_started(self, name, example):
        """Called when a test context begins its run"""
    def context_ended(self, name, example):
        """Called when a test context completes its run"""
    def context_errored(self, name, example, exception):
        """Called when a test context (not an assertion) throws an exception"""

    def assertion_started(self, name):
        """Called when an assertion begins"""
    def assertion_passed(self, name):
        """Called when an assertion passes"""
    def assertion_errored(self, name, exception):
        """Called when an assertion throws an exception"""
    def assertion_failed(self, name, exception):
        """Called when an assertion throws an AssertionError"""

    def unexpected_error(self, exception):
        """Called when an error occurs outside of a Context or Assertion"""

    def identify_method(self, func):
        """
        Called when the test runner encounters a method on a test class and wants to
        know if it should run the method.

        When a test class has a superclass, all the superclass's methods will be passed in first.

        Arguments:
            func - the unbound method (or bound classmethod) which the test runner wants to be identified

        Plugins may return:
            contexts.plugins.EXAMPLES - plugin wishes the method to be treated as an 'examples' method
            contexts.plugins.SETUP - plugin wishes the method to be treated as an 'establish' method
            contexts.plugins.ACTION - plugin wishes the method to be treated as a 'because'
            contexts.plugins.ASSERTION - plugin wishes the method to be treated as an assertion method
            contexts.plugins.TEARDOWN - plugin wishes the method to be treated as a teardown method
            None - plugin does not wish to identify the method (though other plugins may still cause it to be run)
        """

    def process_module_list(self, modules):
        """Called with the full list of found modules. Plugins may modify the list in-place."""
    def process_class_list(self, modules):
        """Called with the list of classes found in a module. Plugins may modify the list in-place."""
    def process_assertion_list(self, modules):
        """Called with the list of assertion methods found in a class. Plugins may modify the list in-place."""

    def import_module(self, location, name):
        """
        Called when the test runner wants a module imported.
        Plugins may return an imported module object, or None if they do not want to import the module.

        Arguments:
            location: string. Path to the folder containing the module or package.
            name: string. Full name of the module, including dot-separated package names.
        """

    def get_exit_code(self):
        """
        Called at the end of the test runner to obtain the exit code for the process.
        Plugins may return an integer, or None if they do not want to override the default behaviour.
        """


EXAMPLES = "examples - DO NOT RELY ON THE VALUE OF THIS CONSTANT"
SETUP = "setup - DO NOT RELY ON THE VALUE OF THIS CONSTANT"
ACTION = "action - DO NOT RELY ON THE VALUE OF THIS CONSTANT"
ASSERTION = "assertion - DO NOT RELY ON THE VALUE OF THIS CONSTANT"
TEARDOWN = "teardown - DO NOT RELY ON THE VALUE OF THIS CONSTANT"


from . import shared, cli, teamcity
