class SpyReporter(object):
    # unittest.mock doesn't make it particularly easy to get hold of the
    # object a mock was called with. It was quicker just to write this myself.
    def __init__(self):
        self.calls = []
        self.failed = False

    def test_run_started(self):
        self.calls.append(('test_run_started',))
    def test_run_ended(self):
        self.calls.append(('test_run_ended',))

    def suite_started(self, name):
        self.calls.append(('suite_started', name))
    def suite_ended(self, name):
        self.calls.append(('suite_ended', name))

    def context_started(self, name, example):
        self.calls.append(('context_started', name, example))
    def context_ended(self, name, example):
        self.calls.append(('context_ended', name, example))
    def context_errored(self, name, example, exception):
        self.calls.append(('context_errored', name, example, exception))

    def assertion_started(self, assertion):
        self.calls.append(('assertion_started', assertion))
    def assertion_passed(self, assertion):
        self.calls.append(('assertion_passed', assertion))
    def assertion_errored(self, assertion, exception):
        self.calls.append(('assertion_errored', assertion, exception))

    def assertion_failed(self, assertion, exception):
        self.calls.append(('assertion_failed', assertion, exception))

    def unexpected_error(self, exception):
        self.calls.append(('unexpected_error', exception))
