import sys
from . import core
from . import reporting
from .tools import catch, set_trace, time, setup, action, assertion, teardown, spec


__all__ = ['run', 'main', 'catch', 'set_trace', 'time', 'setup', 'action', 'assertion', 'teardown', 'spec']


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


def run(to_run=None, reporters=None, shuffle=True):
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
    if reporters is None:  # default list of reporters
        reporters = (
            reporting.cli.DotsReporter(sys.stdout),
            reporting.cli.StdOutCapturingReporter(sys.stdout),
            reporting.cli.TimedReporter(sys.stdout)
        )

    notifier = core.ReporterNotifier(*reporters)

    if to_run is None:
        to_run = sys.modules['__main__']

    suite = core.Suite(to_run, shuffle)
    suite.run(notifier)

    return not notifier.failed
