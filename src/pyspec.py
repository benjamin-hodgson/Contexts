import inspect


def no_op():
    pass

def run(spec):
    establish = no_op
    because = no_op
    shoulds = []
    cleanup = no_op

    for name, meth in inspect.getmembers(spec, inspect.ismethod):
        if "establish" in name:
            establish = meth
        if "because" in name:
            because = meth
        if "should" in name:
            shoulds.append(meth)
        if "cleanup" in name:
            cleanup = meth

    establish()
    because()
    for should in shoulds:
        should()
    cleanup()
