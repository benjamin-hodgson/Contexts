Plugins
=======

Contexts features an experimental 'plugin' interface for user-customisable behaviour.

.. contents::

The plugin interface
--------------------
For documentation purposes, the full plugin interface is defined in :class:`~contexts.plugin_interface.PluginInterface`.
Currently, plugins are **required** to implement the :meth:`~contexts.plugin_interface.PluginInterface.initialise` method (to determine whether the plugin is active in the current test run). The rest of the plugin interface is optional.

Contexts's plugin support is implemented as an ordered list of plugin classes. Each time a plugin hook is called, each plugin is called in turn. Plugins which do not implement the hook are skipped. The *first* return value is used as the return value of the aggregated plugin calls - when a plugin returns a value from a hook, all the remaining plugins in the list are skipped. This means that a given plugin is able to override the behaviour of plugins which follow it in the list.


.. _lifecycle:

The plugin lifecycle
--------------------
Because plugins can override one another, the ordering of the list matters. The interface defines a :func:`classmethod <classmethod>` entitled :meth:`~contexts.plugin_interface.PluginInterface.locate`, which you can implement to insert your plugin before or after another plugin.

Plugins are given control over whether or not they appear in the list. All plugins **must** define an :meth:`initialise(args, environ) <contexts.plugin_interface.PluginInterface.initialise>` method, and return either ``True`` or ``False`` to signal whether they want to appear in the list. You may also define a :meth:`setup_parser(parser) <contexts.plugin_interface.PluginInterface.setup_parser>` method to modify the :class:`argparse.ArgumentParser` instance that is used to parse command-line arguments.

Very occasionally, it is necessary for plugins to modify the behaviour of other plugin objects (see :class:`FailuresOnly` for an example) - you can define a :meth:`~contexts.plugin_interface.PluginInterface.request_plugins` generator method to request the current instances of some other plugin classes from the test runner.


.. _progress:

Progress notifications
----------------------
There exist a number of plugin hooks which are called when progress through the test run reaches certain points. These methods include :meth:`~contexts.plugin_interface.PluginInterface.test_run_started`, :meth:`~contexts.plugin_interface.PluginInterface.context_ended`, :meth:`~contexts.plugin_interface.PluginInterface.assertion_failed`, and so on.

These hooks are typically used to report progress to the user. It's not recommended to return a value from these methods, unless you want to prevent other plugins from being told about the progress.


.. _identifying:

Identifying test objects
------------------------
When the test runner sees a file, folder, class, or method, it queries the list of plugins to find out whether it should run it, using the :meth:`~contexts.plugin_interface.PluginInterface.identify_folder`, :meth:`~contexts.plugin_interface.PluginInterface.identify_file`, :meth:`~contexts.plugin_interface.PluginInterface.identify_class`, and :meth:`~contexts.plugin_interface.PluginInterface.identify_method` hooks. The expected return values from these methods are defined as constants in the :mod:`contexts.plugin_interface` module: :const:`~contexts.plugin_interface.TEST_FILE`, :const:`~contexts.plugin_interface.CONTEXT`, :const:`~contexts.plugin_interface.ASSERTION` and so on.

After all the modules have been imported, the :meth:`~contexts.plugin_interface.PluginInterface.process_module_list` hook is called, which plugins can use to inject their own test modules, or remove modules that should not be run. There are also :meth:`~contexts.plugin_interface.PluginInterface.process_class_list` and :meth:`~contexts.plugin_interface.PluginInterface.process_assertion_list` hooks.


.. _other:

Other hooks
-----------
There are a few extra plugin hooks to override the way modules are imported (see :class:`AssertionRewritingImporter` for an example) and to set the exit code for the process.


Registering a plugin
--------------------
Once you've written your plugin, you can register it with Contexts using the ``contexts.plugins`` `Setuptools entry point <http://pythonhosted.org/setuptools/setuptools.html#dynamic-discovery-of-services-and-plugins>`_:

::

    from setuptools import setup

    setup(
        # ...
        entry_points = {
            'contexts.plugins': ['MyPluginClass = my_package.my_module:MyPluginClass']
        }
        # ...
    )


The plugin API
--------------

.. automodule:: contexts.plugin_interface

.. autoclass:: PluginInterface
    :members:

.. autodata:: TEST_FOLDER
    :annotation:

.. autodata:: TEST_FILE
    :annotation:

.. autodata:: CONTEXT
    :annotation:

.. autodata:: EXAMPLES
    :annotation:

.. autodata:: SETUP
    :annotation:

.. autodata:: ACTION
    :annotation:

.. autodata:: ASSERTION
    :annotation:

.. autodata:: TEARDOWN
    :annotation:

.. autodata:: NO_EXAMPLE
    :annotation:
