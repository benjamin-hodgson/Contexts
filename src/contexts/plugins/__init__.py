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

    def process_module_list(self, modules):
        """Called with the full list of found modules. Plugins may modify the list in-place."""
    def process_class_list(self, modules):
        """Called with the list of classes found in a module. Plugins may modify the list in-place."""
    def process_assertion_list(self, modules):
        """Called with the list of assertion methods found in a class. Plugins may modify the list in-place."""

from . import shared, cli, teamcity
