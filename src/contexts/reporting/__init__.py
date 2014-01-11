class Reporter(object):
    """
    Interface for a reporter object
    """
    def test_run_started(self, test_run):
        """Called at the beginning of a test run"""

    def test_run_ended(self, test_run):
        """Called at the end of a test run"""

    def suite_started(self, suite):
        """Called at the start of a test module"""

    def suite_ended(self, suite):
        """Called at the end of a test module"""

    def unexpected_error(self, exception):
        """Called when an error occurs outside of a Context or Assertion"""

    def context_started(self, name, example):
        """Called when a test context begins its run"""

    def context_ended(self, name, example):
        """Called when a test context completes its run"""

    def context_errored(self, name, example, exception):
        """Called when a test context (not an assertion) throws an exception"""

    def assertion_started(self, assertion):
        """Called when an assertion begins"""

    def assertion_passed(self, assertion):
        """Called when an assertion passes"""

    def assertion_errored(self, assertion, exception):
        """Called when an assertion throws an exception"""

    def assertion_failed(self, assertion, exception):
        """Called when an assertion throws an AssertionError"""

from . import shared, cli, teamcity
