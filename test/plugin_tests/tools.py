import collections
from contexts.plugin_interface import NO_EXAMPLE


class FakeCode(object):
    def __init__(self, co_filename, co_name):
        self.co_filename = co_filename
        self.co_name = co_name


class FakeFrame(object):
    def __init__(self, f_code, source):
        self.f_code = f_code
        self.f_globals = {'__loader__': FakeLoader(source),
                          '__name__': f_code.co_filename[:-3]}


class FakeTraceback(object):
    def __init__(self, frames, line_nums):
        if len(frames) != len(line_nums):
            raise ValueError("Ya messed up!")
        self._frames = frames
        self._line_nums = line_nums
        self.tb_frame = frames[0]
        self.tb_lineno = line_nums[0]

    @property
    def tb_next(self):
        if len(self._frames) > 1:
            return FakeTraceback(self._frames[1:], self._line_nums[1:])


class FakeException(Exception):
    def __init__(self, *args):
        self._tb = None
        self.__context__ = None
        self.__cause__ = None
        super().__init__(*args)

    @property
    def __traceback__(self):
        return self._tb

    @__traceback__.setter
    def __traceback__(self, value):
        pass

    def with_traceback(self, value):
        self._tb = value
        return self


class FakeAssertionError(FakeException, AssertionError):
    pass


class FakeLoader(object):
    def __init__(self, source):
        self.source = source

    def get_source(self, name):
        return self.source


def build_fake_exception(tb_list, *args, cls=FakeException):
    exc = cls(*args)

    frames = []
    line_nums = []

    for filename, lineno, funcname, line in tb_list:
        code = FakeCode(filename, funcname)
        source_list = [''] * (lineno - 1)
        source_list.append(line)
        source = '\n'.join(source_list)
        frames.append(FakeFrame(code, source))
        line_nums.append(lineno)

    tb = FakeTraceback(frames, line_nums)
    return exc.with_traceback(tb)


def build_fake_assertion_error(*args):
    return build_fake_exception(*args, cls=FakeAssertionError)


context_spec = collections.namedtuple("context_spec", ["cls", "name", "example"])


def create_context(name='context', example=NO_EXAMPLE):
    cls = type(name, (), {})
    return context_spec(cls, name, example)
