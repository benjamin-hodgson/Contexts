import traceback
from .core import Result


class TextResult(Result):
    def format_result(self):
        report = self.format_failures()
        report += "----------------------------------------------------------------------\n"
        report += self.failure_summary() if self.failed else self.success_summary()
        return report

    def format_failures(self):
        return "".join([format_assertion_failure(a, e, t) for a, e, t in self.assertion_errors + self.assertion_failures])

    def success_summary(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        msg = """PASSED!
{}, {}
""".format(pluralise("context", num_ctx), pluralise("assertion", num_ass))
        return msg

    def failure_summary(self):
        num_ctx = len(self.contexts)
        num_ass = len(self.assertions)
        num_fail = len(self.assertion_failures)
        num_err = len(self.assertion_errors)
        msg =  """FAILED!
{}, {}: {} failed, {}
""".format(pluralise("context", num_ctx),
           pluralise("assertion", num_ass),
           num_fail,
           pluralise("error", num_err))
        return msg

def format_assertion_failure(assertion, exc, extracted_tb):
    msg = "======================================================================\n"
    msg += "FAIL: " if isinstance(exc, AssertionError) else "ERROR: "
    msg += assertion.name + '\n'
    msg += "----------------------------------------------------------------------\n"
    msg += "Traceback (most recent call last):\n"
    msg += ''.join(traceback.format_list(extracted_tb)) + ''.join(traceback.format_exception_only(exc.__class__, exc))
    return msg


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string
