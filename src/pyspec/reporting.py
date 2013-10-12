import traceback


class Result(object):
    def __init__(self):
        self.contexts = []
        self.assertions = []
        self.context_errors = []
        self.assertion_errors = []
        self.assertion_failures = []

    @property
    def failed(self):
        return self.context_errors or self.assertion_errors or self.assertion_failures

    def add_context(self, context):
        self.contexts.append(context)

    def add_contexts(self, contexts):
        self.contexts.extend(contexts)

    def context_errored(self, context, exception):
        self.context_errors.append((context, exception))

    def add_assertion(self, assertion):
        self.assertions.append(assertion)

    def add_assertions(self, assertions):
        self.assertions.extend(assertions)

    def assertion_errored(self, assertion, exception):
        self.assertion_errors.append((assertion, exception))

    def assertion_failed(self, assertion, exception):
        self.assertion_failures.append((assertion, exception))

def format_result(result):
    report = format_failures(result.assertion_errors + result.assertion_failures)
    report += "----------------------------------------------------------------------\n"
    report += failure_summary(result) if result.failed else success_summary(result)
    return report


def format_failures(failures):
    return "".join([format_failure(a, e) for a, e in failures])


def format_failure(assertion, exc):
    msg = "======================================================================\n"
    msg += "FAIL: " if isinstance(exc, AssertionError) else "ERROR: "
    msg += assertion.name + '\n'
    msg += "----------------------------------------------------------------------\n"
    msg += "Traceback (most recent call last):\n"
    msg += ''.join(traceback.format_list(exc.tb)) + ''.join(traceback.format_exception_only(exc.__class__, exc))
    return msg


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string


def failure_summary(result):
    num_ctx = len(result.contexts)
    num_ass = len(result.assertions)
    num_fail = len(result.assertion_failures)
    num_err = len(result.assertion_errors)
    msg =  """FAILED!
{}, {}: {} failed, {}
""".format(pluralise("context", num_ctx),
       pluralise("assertion", num_ass),
       num_fail,
       pluralise("error", num_err))
    return msg


def success_summary(result):
    num_ctx = len(result.contexts)
    num_ass = len(result.assertions)
    msg = """PASSED!
{}, {}
""".format(pluralise("context", num_ctx), pluralise("assertion", num_ass))
    return msg
