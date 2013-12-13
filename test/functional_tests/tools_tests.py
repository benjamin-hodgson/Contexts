import types
from unittest import mock
import contexts


class WhenMarkingAnUnrelatedMethodAsSetup:
    def context(self):
        class Spec:
            log = ''
            @contexts.setup
            def innocuous_method(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_setup(self):
        assert self.spec.log == "arrange act assert teardown "

class WhenMarkingAnOtherwiseNamedMethodAsSetup:
    def context(self):
        class Spec:
            log = ''
            @contexts.setup
            def when(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_setup(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenMarkingAnUnrelatedMethodAsAction:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            @contexts.action
            def innocuous_method(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_action(self):
        assert self.spec.log == "arrange act assert teardown "

class WhenMarkingAnOtherwiseNamedMethodAsAction:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            @contexts.action
            def context(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_action(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenMarkingAnUnrelatedMethodAsAssertion:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            @contexts.assertion
            def innocuous_method(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_assertion(self):
        assert self.spec.log == "arrange act assert teardown "

class WhenMarkingAnOtherwiseNamedMethodAsAssertion:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            @contexts.assertion
            def context(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_assertion(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenMarkingAnUnrelatedMethodAsTeardown:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            @contexts.teardown
            def innocuous_method(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_teardown(self):
        assert self.spec.log == "arrange act assert teardown "

class WhenMarkingAnOtherwiseNamedMethodAsTeardown:
    def context(self):
        class Spec:
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            @contexts.teardown
            def when(self):
                self.__class__.log += "teardown "
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_teardown(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenMarkingAnUnrelatedMethodAsExamples:
    def context(self):
        class Spec:
            log = []
            @contexts.examples
            @classmethod
            def innocuous_classmethod(self):
                yield 1
                yield 2
            def it(self, example):
                self.__class__.log.append(example)
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_teardown(self):
        assert self.spec.log == [1,2]

class WhenMarkingAnOtherwiseNamedMethodAsExamples:
    def context(self):
        class Spec:
            log = []
            @contexts.examples
            @classmethod
            def because(self):
                yield 1
                yield 2
            def it(self, example):
                self.__class__.log.append(example)
        self.spec = Spec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_treat_the_marked_method_as_teardown(self):
        assert self.spec.log == [1,2]


class WhenMarkingAClassAsASpec:
    def context(self):
        @contexts.spec
        class LovelyClass(object):
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = LovelyClass
        self.module = types.ModuleType("a_module")
        self.module.LovelyClass = LovelyClass

    def because_we_run_the_module(self):
        contexts.run(self.module, [])

    def it_should_treat_the_marked_class_as_a_spec(self):
        assert self.spec.log == "arrange act assert teardown "

class WhenMarkingAClassAsAContext:
    def context(self):
        @contexts.context
        class LovelyClass(object):
            log = ''
            def establish(self):
                self.__class__.log += "arrange "
            def because(self):
                self.__class__.log += "act "
            def it(self):
                self.__class__.log += "assert "
            def cleanup(self):
                self.__class__.log += "teardown "
        self.spec = LovelyClass
        self.module = types.ModuleType("a_module")
        self.module.LovelyClass = LovelyClass

    def because_we_run_the_module(self):
        contexts.run(self.module, [])

    def it_should_treat_the_marked_class_as_a_spec(self):
        assert self.spec.log == "arrange act assert teardown "


class WhenCatchingAnException:
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec:
            exception = None
            def context(s):
                def throwing_function(a, b, c, d=[]):
                    s.__class__.call_args = (a,b,c,d)
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.__class__.exception = contexts.catch(s.throwing_function, 3, c='yes', b=None)

        self.spec = TestSpec

    def because_we_run_the_spec(self):
        contexts.run(self.spec, [])

    def it_should_catch_and_return_the_exception(self):
        assert self.spec.exception == self.exception

    def it_should_call_it_with_the_supplied_arguments(self):
        assert self.spec.call_args == (3, None, 'yes', [])


class WhenTimingSomething:
    def context(self):
        self.mock_clock = mock.Mock(return_value = 10)
        self.time_diff = 100.7
        def slow_function(a,b,c,d=[]):
            self.call_args = (a,b,c,d)
            self.mock_clock.return_value += self.time_diff
        self.slow_function = slow_function

    def because_we_run_a_slow_function(self):
        with mock.patch("time.time", self.mock_clock):
            self.result = contexts.time(self.slow_function, 3, c='yes', b=None)

    def it_should_call_the_function_with_the_supplied_arguments(self):
        assert self.call_args == (3, None, 'yes', [])

    def it_should_return_the_time_difference_in_seconds(self):
        assert self.result == self.time_diff
