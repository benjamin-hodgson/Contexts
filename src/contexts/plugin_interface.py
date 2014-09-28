class PluginInterface(object):
    """
    Defines the interface for plugins.

    You do not need to inherit from this class in your own plugins.
    Just create a new class and implement `initialise` (and one or more other hooks).
    """
    @classmethod
    def locate(cls):
        """
        Called before the plugin is instantiated, to determine where it should
        appear in the list of plugins.
        The ordering of this list matters. If a plugin returns a (non-``None``) value
        from a given method, plugins later in the list will not get called.

        Plugins may return a 2-tuple of ``(left, right)``.
        Here, ``left`` is a plugin class which this plugin wishes to *follow*,
        and ``right`` is a class the plugin wishes to *precede*.
        Either or both of the values may be `None`, to indicate that the plugin
        does not mind what it comes before or after, respectively.
        Returning ``None`` from this method is equivalent to returning ``(None, None)``.
        """
    def setup_parser(self, parser):
        """
        Called before command-line arguments are parsed.

        :param parser: An instance of :class:`argparse.ArgumentParser`.
            Plugins may mutate ``parser`` in order to set it up to expect the options
            the plugin needs to configure itself. See the standard library documentation
            for :mod:`argparse` for more information.
        """
    def initialise(self, args, environ):
        """
        Called after command-line arguments are parsed.

        :param args: The result of :meth:`ArgumentParser.parse_args <argparse.ArgumentParser.parse_args>`.
            (see the standard library documentation for :mod:`argparse` for more information).
        :param environ: The value of :data:`os.environ`.

        :return: A boolean. Returning ``True`` will cause the plugin to be added to the list of plugins
            for this test run. Returning ``False`` will prevent this.
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
        """Called at the beginning of a test run."""
    def test_run_ended(self):
        """Called at the end of a test run."""

    def suite_started(self, module):
        """
        Called at the start of a test module.

        :param module: The Python module (an instance of :class:`~types.ModuleType`) that is about to be run.
        """
    def suite_ended(self, module):
        """
        Called at the end of a test module.

        :param module: The Python module (an instance of :class:`~types.ModuleType`) that was just run.
        """

    def test_class_started(self, cls):
        """
        Called when a test class begins its run.

        A test class may contain one or more test contexts.
        (Test classes with examples will generally contain more than one.)

        :param cls: The class object that is being run.
        """
    def test_class_ended(self, cls):
        """
        Called when a test class ends its run.

        :param cls: The class object that is being run.
        """
    def test_class_errored(self, cls, exception):
        """
        Called when a test class unexpectedly errors.

        :param cls: The class object that is being run.
        :param exception: The exception that got caused the error.
        """

    def context_started(self, cls, example):
        """
        Called when a test context begins its run.

        :param cls: The class object of the test being run.
        :param example: The current example, which may be :const:`~contexts.plugin_interface.NO_EXAMPLE`
            if it is not a parametrised test.
        """
    def context_ended(self, cls, example):
        """
        Called when a test context completes its run.

        :param cls: The class object of the test being run.
        :param example: The current example, which may be :const:`~contexts.plugin_interface.NO_EXAMPLE`
            if it is not a parametrised test.
        """
    def context_errored(self, cls, example, exception):
        """
        Called when a test context (not an assertion) throws an exception.

        :param cls: The class object of the test being run.
        :param example: The current example, which may be :const:`~contexts.plugin_interface.NO_EXAMPLE`
            if it is not a parametrised test.
        :param exception: The exception that caused the error.
        """

    def assertion_started(self, func):
        """
        Called when an assertion begins.

        :param func: The assertion method being run.
        """
    def assertion_passed(self, func):
        """
        Called when an assertion passes.

        :param func: The assertion method being run.
        """
    def assertion_errored(self, func, exception):
        """
        Called when an assertion throws an exception.

        :param func: The assertion method being run.
        :param exception: The exception that caused the error.
        """
    def assertion_failed(self, func, exception):
        """
        Called when an assertion throws an AssertionError.

        :param func: The assertion method being run.
        :param exception: The exception that caused the failure.
        """

    def unexpected_error(self, exception):
        """
        Called when an error occurs outside of a Context or Assertion.

        :param exception: The exception that caused the failure.
        """

    def get_object_to_run(self):
        """
        Called before the start of the test run, when the test runner wants to know
        what it should run.

        This method should return one of:
            * a class - the test runner will run the identified methods in this class.
            * a file path as a string - the test runner will run the identified classes in this file.
            * a folder path as a string - the test runner will run the identified files and subfolders in this folder.
            * ``None`` - the plugin doesn't want to choose what to run.
        """
    def identify_folder(self, folder):
        """
        Called when the test runner encounters a folder and wants to know if it should
        run the tests in that folder.

        :param folder str: The full path of the folder which the test runner wants to be identified

        This method should return one of:
            * :const:`~contexts.plugin_interface.TEST_FOLDER` - plugin wishes the folder to be treated as a test folder
            * ``None`` - plugin does not wish to identify the folder (though other plugins may still cause it to be run)
        """
    def identify_file(self, file):
        """
        Called when the test runner encounters a file and wants to know if it should
        run the tests in that file.

        :param file str: The full path of the file which the test runner wants to be identified.

        This method should return one of:
            * :const:`~contexts.plugin_interface.TEST_FILE` - plugin wishes the file to be imported and run as a test file
            * ``None`` - plugin does not wish to identify the file (though other plugins may still cause it to be run)
        """
    def identify_class(self, cls):
        """
        Called when the test runner encounters a class and wants to know if it should
        treat it as a test class.

        :param cls: The class object which the test runner wants to be identified.

        This method should return one of:
            * :const:`~contexts.plugin_interface.CONTEXT` - plugin wishes the class to be treated as a test class
            * ``None`` - plugin does not wish to identify the class (though other plugins may still cause it to be run)
        """
    def identify_method(self, func):
        """
        Called when the test runner encounters a method on a test class and wants to
        know if it should run the method.

        When a test class has a superclass, all the superclass's methods will be passed in first.

        :param func: The unbound method (or bound classmethod) which the test runner wants to be identified

        This method should return one of:
            * :const:`~contexts.plugin_interface.EXAMPLES` - plugin wishes the method to be treated as an 'examples' method
            * :const:`~contexts.plugin_interface.SETUP` - plugin wishes the method to be treated as an 'establish' method
            * :const:`~contexts.plugin_interface.ACTION` - plugin wishes the method to be treated as a 'because'
            * :const:`~contexts.plugin_interface.ASSERTION` - plugin wishes the method to be treated as an assertion method
            * :const:`~contexts.plugin_interface.TEARDOWN` - plugin wishes the method to be treated as a teardown method
            * ``None`` - plugin does not wish to identify the method (though other plugins may still cause it to be run)
        """

    def process_module_list(self, modules):
        """
        A hook to change (or examine) the list of modules which will be run with the full list of found modules.
        Plugins may modify the list in-place by adding or removing modules.

        :param modules: A list of :class:`types.ModuleType`.
        """
    def process_class_list(self, module, classes):
        """
        A hook to change (or examine) the list of classes found in a module.
        Plugins may modify the list in-place by adding or removing classes.

        :param module: The Python module in which the classes were found (an instance of :class:`types.ModuleType`).
        :param classes: A list of classes found in that module.
        """
    def process_assertion_list(self, cls, functions):
        """
        A hook to change (or examine) the list of (unbound) assertion methods found in a class.
        Plugins may modify the list in-place by adding or removing functions.

        :param cls: The test class in which the methods were found
        :param functions: A list of unbound assertion methods found in that class
        """

    def import_module(self, location, name):
        """
        Called when the test runner needs to import a module.

        Arguments:
            location: string. Path to the folder containing the module or package.
            name: string. Full name of the module, including dot-separated package names.

        This method should return one of:
            * an imported module (an instance of :class:`types.ModuleType`).
                This may be a reference to an existing module, or a "fake" generated module.
            * ``None``, if the plugin is not able to import the module.
        """

    def get_exit_code(self):
        """
        Called at the end of the test runner to obtain the exit code for the process.

        This method should return one of:
            * An integer
            * ``None``, if you do not want to override the default behaviour.
        """


#: Returned by plugins to indicate that a folder contains tests.
TEST_FOLDER = type("_TestFolder", (), {})()
#: Returned by plugins to indicate that a file contains tests.
TEST_FILE = type("_TestFile", (), {})()
#: Returned by plugins to indicate that a class is a test class.
CONTEXT = type("_Context", (), {})()
#: Returned by plugins to indicate that a method is an Examples method.
EXAMPLES = type("_Examples", (), {})()
#: Returned by plugins to indicate that a method is a setup method.
SETUP = type("_Setup", (), {})()
#: Returned by plugins to indicate that a method is an action method.
ACTION = type("_Action", (), {})()
#: Returned by plugins to indicate that a method is an assertion method.
ASSERTION = type("_Assertion", (), {})()
#: Returned by plugins to indicate that a method is a teardown method.
TEARDOWN = type("_Teardown", (), {})()
#: Passed to plugins when a class is not a parametrised test.
NO_EXAMPLE = type("_NoExample", (), {})()
