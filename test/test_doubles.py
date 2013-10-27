class MockResult(object):
    # unittest.mock doesn't make it particularly easy to get hold of the
    # object a mock was called with. It was quicker just to write this myself.
    def __init__(self):
        self.calls = []
        self.failed = False

    def suite_started(self, suite):
        self.calls.append(('suite_started', suite))

    def suite_ended(self, suite):
        self.calls.append(('suite_ended', suite))

    def context_started(self, context):
        self.calls.append(('context_started', context))

    def context_ended(self, context):
        self.calls.append(('context_ended', context))

    def context_errored(self, context, exception, extracted_traceback):
        self.calls.append(('context_errored', context, exception, extracted_traceback))

    def assertion_started(self, assertion):
        self.calls.append(('assertion_started', assertion))

    def assertion_passed(self, assertion):
        self.calls.append(('assertion_passed', assertion))

    def assertion_errored(self, assertion, exception, extracted_traceback):
        self.calls.append(('assertion_errored', assertion, exception, extracted_traceback))

    def assertion_failed(self, assertion, exception, extracted_traceback):
        self.calls.append(('assertion_failed', assertion, exception, extracted_traceback))
