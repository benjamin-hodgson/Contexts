def setup(func):
    func._contexts_role = "establish"
    return func

def action(func):
    func._contexts_role = "because"
    return func

def assertion(func):
    func._contexts_role = "should"
    return func

def teardown(func):
    func._contexts_role = "cleanup"
    return func

def spec(cls):
    cls._contexts_role = "Spec"
    return cls
