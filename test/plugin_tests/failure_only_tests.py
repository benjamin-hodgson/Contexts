from io import StringIO
from contexts.plugins.cli import FailuresOnlyMaster, FailuresOnlyBefore, FailuresOnlyAfter


class WhenAnUnexpectedErrorOccurs:
    def context(self):
        self.master = FailuresOnlyMaster(StringIO())
        self.before = FailuresOnlyBefore()
        self.after = FailuresOnlyAfter()

        send_instances(self.master, [])
        send_instances(self.before, [self.master])
        send_instances(self.after, [self.master])

    def because_an_unexpected_error_occurs(self):
        self.before.unexpected_error(Exception())

    def it_should_be_ok(self):
        pass


def send_instances(plug, instances):
    gen = plug.request_plugins()
    next(gen)
    try:
        gen.send({type(x): x for x in instances})
    except StopIteration:
        pass
