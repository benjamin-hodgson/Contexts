import traceback


def format_result(result):
    report = format_assertions(result.errors + result.failures)
    report += "----------------------------------------------------------------------\n"
    report += failure_summary(result) if result.failures or result.errors else success_summary(result)
    return report


def format_assertions(assertions):
    return "".join([format_assertion(a) for a in assertions])


def format_assertion(assertion):
    exc = assertion.exception
    msg = "======================================================================\n"
    msg += "FAIL: " if isinstance(exc, AssertionError) else "ERROR: "
    msg += assertion.name + '\n'
    msg += "----------------------------------------------------------------------\n"
    msg += ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return msg


def pluralise(noun, num):
    string = str(num) + ' ' + noun
    if num != 1:
        string += 's'
    return string


def failure_summary(result):
    num_ctx = len(result.contexts)
    num_ass = len(result.assertions)
    num_fail = len(result.failures)
    num_err = len(result.errors)
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
