import sys
from . import builders
from . import reporting
from . import core


__all__ = ['run', 'main', 'catch', 'set_trace']


def main():
    """
    Find and run any test classes in the main file.
    """
    passed = run()
    if not passed:
        sys.exit(1)
    sys.exit(0)


def run(spec=None, reporter=None):
    if reporter is None:
        reporter = reporting.CapturingCLIReporter()
    if spec is None:
        spec = sys.modules['__main__']

    _run_impl(spec, reporter)

    return not reporter.failed


def _run_impl(spec, reporter):
    notifier = core.ReporterNotifier(reporter)
    suite = builders.build_suite(spec)
    suite.run(notifier)


def catch(func, *args, **kwargs):
    """
    Call the supplied function with the supplied arguments,
    catching and returning any exception that it throws.

    Arguments:
        func: the function to run.
        *args: positional arguments to pass into the function.
        **kwargs: keyword arguments to pass into the function.
    Returns:
        If the function throws an exception, return the exception.
        If the function does not throw an exception, return None.
    """
    try:
        func(*args, **kwargs)
    except Exception as e:
        return e


def set_trace():
    # https://github.com/nose-devs/nose/blob/master/nose/tools/nontrivial.py
    import pdb
    import sys
    pdb.Pdb(stdout=sys.__stdout__).set_trace(sys._getframe().f_back)

