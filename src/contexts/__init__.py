import sys
from . import core
from .plugin_discovery import load_plugins
from .tools import catch, set_trace, time
from .plugins.identification.decorators import context, spec, scenario, examples, setup, action, assertion, teardown
from .plugins.test_target_suppliers import ObjectSupplier


__all__ = [
    'run', 'main', 'run_with_plugins',
    'catch', 'set_trace', 'time',
    'context', 'spec', 'scenario', 'examples', 'setup', 'action', 'assertion', 'teardown'
]


def main():
    """
    Call contexts.run() with the sepcified arguments,
    exiting with code 0 if the test run was successful,
    code 1 if unsuccessful.
    """
    plugin_list = load_plugins()

    module = sys.modules['__main__']
    plugin_list.insert(0, ObjectSupplier(module))

    exit_code = run_with_plugins(plugin_list)
    sys.exit(exit_code)


def run():
    """
    Run all the test classes in the main module.

    Returns: exit code as an integer.
        The default behaviour (which may be overridden by plugins) is to return a 0
        exit code if the test run succeeded, and 1 if it failed.
    """
    plugin_list = load_plugins()

    module = sys.modules['__main__']
    plugin_list.insert(0, ObjectSupplier(module))

    return run_with_plugins(plugin_list)


def run_with_plugins(plugin_list):
    """
    Carry out a test run with the supplied list of plugin instances.
    The plugins are expected to identify the object to run.

    Parameters:
        plugin_list: a list of plugin instances (objects which implement some subset of PluginInterface)
    Returns: exit code as an integer.
        The default behaviour (which may be overridden by plugins) is to return a 0
        exit code if the test run succeeded, and 1 if it failed.
    """
    composite = core.PluginComposite(plugin_list)

    to_run = composite.get_object_to_run()

    test_run = core.TestRun(to_run, composite)
    test_run.run()

    return composite.get_exit_code()

