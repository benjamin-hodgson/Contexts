import types
import sure
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
        self.spec.log.should.equal("arrange act assert teardown ")

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
        self.spec.log.should.equal("arrange act assert teardown ")


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
        self.spec.log.should.equal("arrange act assert teardown ")

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
        self.spec.log.should.equal("arrange act assert teardown ")


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
        self.spec.log.should.equal("arrange act assert teardown ")

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
        self.spec.log.should.equal("arrange act assert teardown ")


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
        self.spec.log.should.equal("arrange act assert teardown ")

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
        self.spec.log.should.equal("arrange act assert teardown ")


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
        self.spec.log.should.equal([1,2])

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
        self.spec.log.should.equal([1,2])


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
        self.spec.log.should.equal("arrange act assert teardown ")

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
        self.spec.log.should.equal("arrange act assert teardown ")
