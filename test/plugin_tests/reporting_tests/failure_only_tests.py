from io import StringIO
from contexts.plugins.reporting import cli
import contexts


# TODO: test_class_started, failed, errored, etc

class WhenAnUnexpectedErrorOccurs:
    def context(self):
        self.master = cli.FailuresOnlyMaster(StringIO())
        self.before = cli.FailuresOnlyBefore()
        self.after = cli.FailuresOnlyAfter()

        send_instances(self.master, [])
        send_instances(self.before, [self.master])
        send_instances(self.after, [self.master])

    def because_an_unexpected_error_occurs(self):
        self.exception = contexts.catch(self.before.unexpected_error, Exception())

    def it_should_be_ok(self):
        assert self.exception is None


def send_instances(plug, instances):
    gen = plug.request_plugins()
    next(gen)
    try:
        gen.send({type(x): x for x in instances})
    except StopIteration:
        pass
