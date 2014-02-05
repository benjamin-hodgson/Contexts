class PluginInterface(object):
    """
    Interface for plugins.
    """
    @classmethod
    def locate(cls):
        """
        Called before the plugin is instantiated, to determine where it should
        appear in the list of plugins.
        The ordering of this list matters. If a plugin returns a (non-None) value
        from a given method, plugins later in the list will not get called.

        Plugins may return a 2-tuple of (`left`, `right`).
        Here, `left` is a plugin class which this plugin wishes to _follow_,
        and `right` is a class the plugin wishes to _precede_.
        Either or both of the values may be None, to indicate that the plugin
        does not mind what it comes before or after, respectively.
        Returning None from this method is equivalent to returning (None, None).
        """
    def setup_parser(self, parser):
        """
        Called before command-line arguments are parsed.

        Plugins may mutate `parser`, which is an instance of
        `argparse.ArgumentParser`, in order to set it up to expect the options
        the plugin needs to configure itself. See the standard library documentation
        for `argparse` for more information.
        """
    def initialise(self, args, environ):
        """
        Called after command-line arguments are parsed.

        `args` is the result of `ArgumentParser.parser_args()`.
        (see the standard library documentation for `argparse` for more information).
        `environ` is the value of `os.environ`.
        Plugins should use these to set themselves up.

        Plugins may return True or False from this method. Returning True will cause
        the plugin to be added to the list of plugins for this test run. Returning False
        will prevent this.
        """
    def request_plugins(self):
        """
        Called after all plugins have been initialised.

        Plugins which need to modify the behaviour of other plugins may request
        instances of those plugins from the framework.

        This must be a generator method. Yield an iterable of other plugin classes,
        and you will be sent a dictionary mapping those classes to the active instances
        of those plugins. Requested plugins that do not have an active instance will not be
        present in the dict.
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
        """
        Called when a test context begins its run.

        `name` is the name of the test context. `example` is the current example,
        which may be contexts.plugin_interface.NO_EXAMPLE if it is not a parametrised test.
        """
    def context_ended(self, name, example):
        """
        Called when a test context completes its run

        `name` is the name of the test context. `example` is the current example,
        which may be contexts.plugin_interface.NO_EXAMPLE if it is not a parametrised test.
        """
    def context_errored(self, name, example, exception):
        """
        Called when a test context (not an assertion) throws an exception

        `name` is the name of the test context. `example` is the current example,
        which may be contexts.plugin_interface.NO_EXAMPLE if it is not a parametrised test.
        `exception` is the exception which got thrown.
        """

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

    def identify_folder(self, folder):
        """
        Called when the test runner encounters a folder and wants to know if it should
        run the files in that folder.

        Arguments:
            folder - the full path of the folder which the test runner wants to be identified

        Plugins may return:
            contexts.plugin_interface.TEST_FOLDER - plugin wishes the folder to be treated as a test folder
            None - plugin does not wish to identify the folder (though other plugins may still cause it to be run)
        """
    def identify_file(self, file):
        """
        Called when the test runner encounters a file and wants to know if it should
        run the files in that file.

        Arguments:
            file - the full path of the file which the test runner wants to be identified

        Plugins may return:
            contexts.plugin_interface.TEST_FILE - plugin wishes the file to be imported and run as a test file
            None - plugin does not wish to identify the file (though other plugins may still cause it to be run)
        """
    def identify_class(self, cls):
        """
        Called when the test runner encounters a class and wants to know if it should
        treat it as a test class.

        Arguments:
            cls - the class object which the test runner wants to be identified.

        Plugins may return:
            contexts.plugin_interface.CONTEXT - plugin wishes the class to be treated as a test class
            None - plugin does not wish to identify the class (though other plugins may still cause it to be run)
        """
    def identify_method(self, func):
        """
        Called when the test runner encounters a method on a test class and wants to
        know if it should run the method.

        When a test class has a superclass, all the superclass's methods will be passed in first.

        Arguments:
            func - the unbound method (or bound classmethod) which the test runner wants to be identified

        Plugins may return:
            contexts.plugin_interface.EXAMPLES - plugin wishes the method to be treated as an 'examples' method
            contexts.plugin_interface.SETUP - plugin wishes the method to be treated as an 'establish' method
            contexts.plugin_interface.ACTION - plugin wishes the method to be treated as a 'because'
            contexts.plugin_interface.ASSERTION - plugin wishes the method to be treated as an assertion method
            contexts.plugin_interface.TEARDOWN - plugin wishes the method to be treated as a teardown method
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


TEST_FOLDER = type("_TestFolder", (), {})()
TEST_FILE = type("_TestFile", (), {})()
CONTEXT = type("_Context", (), {})()
EXAMPLES = type("_Examples", (), {})()
SETUP = type("_Setup", (), {})()
ACTION = type("_Action", (), {})()
ASSERTION = type("_Assertion", (), {})()
TEARDOWN = type("_Teardown", (), {})()
NO_EXAMPLE = type("_NoExample", (), {})()
