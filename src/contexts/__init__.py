import sys
from . import core
from .plugin_discovery import load_plugins
from .tools import catch, set_trace, time
from .plugins.identification.decorators import context, spec, examples, setup, action, assertion, teardown


__all__ = [
    'run', 'main',
    'catch', 'set_trace', 'time',
    'context', 'spec', 'examples', 'setup', 'action', 'assertion', 'teardown'
]


def main(*args, **kwargs):
    """
    Call contexts.run() with the sepcified arguments,
    exiting with code 0 if the test run was successful,
    code 1 if unsuccessful.
    """
    exit_code = run(*args, **kwargs)
    sys.exit(exit_code)


# FIXME: run() currently assumes you're running on the cmd line
def run():
    """
    Run all the test classes in the main module.

    Returns: exit code as an integer.
        The default behaviour (which may be overridden by plugins) is to return a 0
        exit code if the test run succeeded, and 1 if it failed.
    """
    plugin_list = load_plugins()
    return run_with_plugins(plugin_list)


def run_with_plugins(plugin_list):
    composite = core.PluginComposite(plugin_list)

    to_run = composite.get_object_to_run()

    test_run = core.TestRun(to_run, composite)
    test_run.run()

    return composite.get_exit_code()

