class SpyReporter(object):
    # unittest.mock doesn't make it particularly easy to get hold of the
    # object a mock was called with. It was quicker just to write this myself.
    def __init__(self):
        self.calls = []
        self.failed = False

    def test_run_started(self, test_run):
        self.calls.append(('test_run_started', test_run))
    def test_run_ended(self, test_run):
        self.calls.append(('test_run_ended', test_run))

    def suite_started(self, suite):
        self.calls.append(('suite_started', suite))
    def suite_ended(self, suite):
        self.calls.append(('suite_ended', suite))

    def context_started(self, context):
        self.calls.append(('context_started', context))
    def context_ended(self, context):
        self.calls.append(('context_ended', context))
    def context_errored(self, context, exception):
        self.calls.append(('context_errored', context, exception))

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


class NullConfiguration(object):
    def process_module_list(self, l):
        pass
    def process_class_list(self, l):
        pass
    def process_assertion_list(self, l):
        pass
    def shuffle_list(self, l):
        pass
