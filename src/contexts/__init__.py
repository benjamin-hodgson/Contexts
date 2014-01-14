import sys
from . import core
from . import plugins
from .tools import (
    catch, set_trace, time,
    setup, action, assertion, teardown, examples,
    spec, context
)


__all__ = [
    'run', 'main',
    'catch', 'set_trace', 'time',
    'setup', 'action', 'assertion', 'teardown', 'examples',
    'spec', 'context'
]


def main(*args, **kwargs):
    """
    Call contexts.run() with the sepcified arguments,
    exiting with code 0 if the test run was successful,
    code 1 if unsuccessful.
    """
    passed = run(*args, **kwargs)
    if not passed:
        sys.exit(1)
    sys.exit(0)


def run(to_run=None, plugin_list=None):
    """
    Polymorphic test-running function.

    run() - run all the test classes in the main module
    run(class) - run the test class
    run(module) - run all the test classes in the module
    run(file_path:string) - run all the test classes found in the file
    run(folder_path:string) - run all the test classes found in the folder and subfolders
    run(package_path:string) - run all the test classes found in the package and subfolders

    Returns: True if the test run passed, False if it failed.
    """
    if plugin_list is None:  # default list of plugins
        plugin_list = (
            plugins.cli.DotsReporter(sys.stdout),
            plugins.cli.StdOutCapturingReporter(sys.stdout),
            plugins.cli.TimedReporter(sys.stdout)
        )

    if to_run is None:
        to_run = sys.modules['__main__']

    notifier = core.PluginNotifier(plugin_list)
    test_run = core.TestRun(to_run, notifier)
    test_run.run()

    return not notifier.failed
