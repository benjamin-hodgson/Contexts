from io import StringIO
import os
import shutil
import sys
import types
import sure
import contexts
from contexts import reporting

core_file = repr(contexts.core.__file__)[1:-1]
this_file = repr(__file__)[1:-1]


class WhenRunningASpec(object):
    def context(self):
        self.assertion_err = AssertionError()
        self.value_err = ValueError()

        class TestSpec(object):
            def __init__(s):
                s.log = ""
            def method_with_establish_in_the_name(s):
                s.log += "arrange "
            def method_with_because_in_the_name(s):
                s.log += "act "
            def method_with_should_in_the_name(s):
                s.log += "assert "
            def failing_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.assertion_err
            def erroring_method_with_should_in_the_name(s):
                s.log += "assert "
                raise self.value_err
            def method_with_cleanup_in_the_name(s):
                s.log += "teardown "

        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec.log.should.equal("arrange act assert assert assert teardown ")

    def the_result_should_report_failure(self):
        self.result.failed.should.be.true

    def the_result_should_have_one_ctx(self):
        self.result.contexts.should.have.length_of(1)

    def the_ctx_should_have_the_right_name(self):
        self.result.contexts[0].name.should.equal("TestSpec")

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(3)

    def the_assertions_should_have_the_right_names(self):
        names = [a.name for a in self.result.assertions]
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name')
        names.should.contain(__name__ + '.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name')

    def the_result_should_have_one_failure(self):
        self.result.assertion_failures.should.have.length_of(1)

    def the_failure_should_have_the_right_name(self):
        self.result.assertion_failures[0][0].name.should.equal(
            __name__ + '.WhenRunningASpec.context.<locals>.TestSpec.failing_method_with_should_in_the_name'
        )

    def the_failure_should_have_the_exception(self):
        self.result.assertion_failures[0][1].should.equal(self.assertion_err)

    def the_failure_should_have_the_traceback(self):
        self.result.assertion_failures[0][2].should_not.be.empty

    def the_result_should_have_one_error(self):
        self.result.assertion_errors.should.have.length_of(1)

    def the_error_should_have_the_right_name(self):
        self.result.assertion_errors[0][0].name.should.equal(
            __name__ + '.WhenRunningASpec.context.<locals>.TestSpec.erroring_method_with_should_in_the_name'
        )

    def the_error_should_have_the_exception(self):
        self.result.assertion_errors[0][1].should.equal(self.value_err)

    def the_error_should_have_the_traceback(self):
        self.result.assertion_errors[0][2].should_not.be.empty

class WhenASpecPasses(object):
    def context(self):
        class TestSpec(object):
            def it(self):
                pass
        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def the_result_should_report_success(self):
        self.result.failed.should.be.false

class WhenAContextErrors(object):
    def context(self):
        class ErrorInSetup(object):
            def __init__(self):
                self.ran_cleanup = False
            def context(self):
                raise ValueError("explode")
            def it(self):
                pass
            def cleanup(self):
                self.ran_cleanup = True
        class ErrorInAction(object):
            def __init__(self):
                self.ran_cleanup = False
            def because(self):
                raise TypeError("oh no")
            def it(self):
                pass
            def cleanup(self):
                self.ran_cleanup = True
        class ErrorInTeardown(object):
            def it(self):
                pass
            def cleanup(self):
                raise AttributeError("got it wrong")

        self.specs = [ErrorInSetup(), ErrorInAction(), ErrorInTeardown()]

    def because_we_run_the_specs(self):
        self.results = []
        for spec in self.specs:
            result = contexts.core.Result()
            self.results.append(result)
            contexts.run(spec, result)

    def the_result_should_contain_the_ctx_error(self):
        self.results[0].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_action_error(self):
        self.results[1].context_errors.should.have.length_of(1)

    def the_result_should_contain_the_trdn_error(self):
        self.results[2].context_errors.should.have.length_of(1)

    def it_should_still_run_the_trdn_despite_the_ctx_error(self):
        self.specs[0].ran_cleanup.should.be.true

    def it_should_still_run_the_trdn_despite_the_action_error(self):
        self.specs[1].ran_cleanup.should.be.true

class WhenWeRunSpecsWithAlternatelyNamedMethods(object):
    def context(self):
        class AlternatelyNamedMethods(object):
            def __init__(self):
                self.log = ""
            def has_context_in_the_name(self):
                self.log += "arrange "
            def has_when_in_the_name(self):
                self.log += "act "
            def has_it_in_the_name(self):
                self.log += "assert "
        class MoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_setup_in_the_name(self):
                self.log += "arrange "
            def has_since_in_the_name(self):
                self.log += "act "
            def has_must_in_the_name(self):
                self.log += "assert "
            def has_teardown_in_the_name(self):
                self.log += "cleanup "
        class EvenMoreAlternativeNames(object):
            def __init__(self):
                self.log = ""
            def has_given_in_the_name(self):
                self.log += "arrange "
            def has_after_in_the_name(self):
                self.log += "act "
            def has_will_in_the_name(self):
                self.log += "assert "

        self.spec1 = AlternatelyNamedMethods()
        self.spec2 = MoreAlternativeNames()
        self.spec3 = EvenMoreAlternativeNames()

    def because_we_run_the_specs(self):
        contexts.run(self.spec1, contexts.core.Result())
        contexts.run(self.spec2, contexts.core.Result())
        contexts.run(self.spec3, contexts.core.Result())

    def it_should_run_the_methods_in_the_correct_order(self):
        self.spec1.log.should.equal("arrange act assert ")
        self.spec2.log.should.equal("arrange act assert cleanup ")
        self.spec3.log.should.equal("arrange act assert ")

class WhenRunningAmbiguouslyNamedMethods(object):
    def context(self):
        class AmbiguousMethods1(object):
            def this_has_both_context_and_because_in_the_name(self):
                pass
        class AmbiguousMethods2(object):
            def this_has_both_because_and_should_in_the_name(self):
                pass
        class AmbiguousMethods3(object):
            def this_has_both_should_and_teardown_in_the_name(self):
                pass
        class AmbiguousMethods4(object):
            def this_has_both_teardown_and_establish_in_the_name(self):
                pass

        self.specs = [AmbiguousMethods1(), AmbiguousMethods2(), AmbiguousMethods3(), AmbiguousMethods4()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_raise_MethodNamingError(self):
        self.exceptions[0].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[1].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[2].should.be.a(contexts.errors.MethodNamingError)
        self.exceptions[3].should.be.a(contexts.errors.MethodNamingError)

class WhenRunningNotSoAmbiguouslyNamedMethods(object):
    def context(self):
        class NotAmbiguousMethods1(object):
            def this_has_both_context_and_establish_in_the_name(self):
                pass
        class NotAmbiguousMethods2(object):
            def this_has_both_because_and_when_in_the_name(self):
                pass
        class NotAmbiguousMethods3(object):
            def this_has_both_should_and_it_in_the_name(self):
                pass
        class NotAmbiguousMethods4(object):
            def this_has_both_teardown_and_cleanup_in_the_name(self):
                pass

        self.specs = [NotAmbiguousMethods1(), NotAmbiguousMethods2(), NotAmbiguousMethods3(), NotAmbiguousMethods4()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_not_raise_any_exceptions(self):
        self.exceptions[0].should.be.none
        self.exceptions[1].should.be.none
        self.exceptions[2].should.be.none
        self.exceptions[3].should.be.none

class WhenRunningSpecsWithTooManySpecialMethods(object):
    def context(self):
        class TooManyContexts(object):
            def context(self):
                pass
            def establish(self):
                pass
        class TooManyActions(object):
            def because(self):
                pass
            def when(self):
                pass
        class TooManyTeardowns(object):
            def cleanup(self):
                pass
            def teardown(self):
                pass

        self.specs = [TooManyContexts(), TooManyActions(), TooManyTeardowns()]
        self.exceptions = []

    def because_we_try_to_run_the_specs(self):
        for spec in self.specs:
            self.exceptions.append(contexts.catch(lambda: contexts.run(spec, contexts.core.Result())))

    def it_should_raise_TooManySpecialMethodsError(self):
        self.exceptions[0].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[1].should.be.a(contexts.errors.TooManySpecialMethodsError)
        self.exceptions[2].should.be.a(contexts.errors.TooManySpecialMethodsError)

class WhenCatchingAnException(object):
    def context(self):
        self.exception = ValueError("test exception")

        class TestSpec(object):
            def __init__(s):
                s.exception = None
            def context(s):
                def throwing_function(a, b, c, d=[]):
                    s.call_args = (a,b,c,d)
                    # Looks weird! Referencing 'self' from outer scope
                    raise self.exception
                s.throwing_function = throwing_function
            def should(s):
                s.exception = contexts.catch(s.throwing_function, 3, c='yes', b=None)

        self.spec = TestSpec()
        self.result = contexts.core.Result()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, self.result)

    def it_should_catch_and_return_the_exception(self):
        self.spec.exception.should.equal(self.exception)

    def it_should_call_it_with_the_supplied_arguments(self):
        self.spec.call_args.should.equal((3, None, 'yes', []))

    def it_should_not_have_a_failure_result(self):
        self.result.assertions.should.have.length_of(1)
        self.result.assertion_failures.should.be.empty
        self.result.context_errors.should.be.empty
        self.result.assertion_errors.should.be.empty

class WhenASpecHasASuperclass(object):
    def context(self):
        class SharedContext(object):
            def __init__(self):
                self.log = ""
            def context(self):
                self.log += "superclass arrange "
            def superclass_because(self):
                self.log += "superclass action "
            def it(self):
                self.log += "superclass assertion "
            def cleanup(self):
                self.log += "superclass cleanup "
        class Spec(SharedContext):
            # I want it to run the superclasses' specially-named methods
            # _even if_ they are masked by the subclass
            def context(self):
                self.log += "subclass arrange "
            def because(self):
                self.log += "subclass action "
            def it(self):
                self.log += "subclass assertion "
            def cleanup(self):
                self.log += "subclass cleanup "

        self.spec = Spec()

    def because_we_run_the_spec(self):
        contexts.run(self.spec, contexts.core.Result())

    def it_should_run_the_superclass_ctx_first(self):
        self.spec.log[:19].should.equal("superclass arrange ")

    def it_should_run_the_subclass_ctx_next(self):
        self.spec.log[19:36].should.equal("subclass arrange ")

    def it_should_run_the_subclass_bec_next(self):
        self.spec.log[36:52].should.equal("subclass action ")

    def it_should_not_run_the_superclass_bec(self):
        self.spec.log.should_not.contain("superclass action ")

    def it_should_run_both_assertions(self):
        # We don't care what order the two assertions get run in
        self.spec.log[52:92].should.contain("superclass assertion ")
        self.spec.log[52:92].should.contain("subclass assertion ")

    def it_should_run_the_subclass_clean_first(self):
        self.spec.log[92:109].should.equal("subclass cleanup ")

    def it_should_run_the_superclass_clean_second(self):
        self.spec.log[109:238].should.equal("superclass cleanup ")

class WhenRunningMultipleSpecs(object):
    def context(self):
        class Spec1(object):
            def it(self):
                self.was_run = True
        class Spec2(object):
            def it(self):
                self.was_run = True

        self.suite = [Spec1(), Spec2()]
        self.result = contexts.core.Result()

    def because_we_run_the_suite(self):
        contexts.run(self.suite, self.result)

    def it_should_run_both_tests(self):
        self.suite[0].was_run.should.be.true
        self.suite[1].was_run.should.be.true

    def the_result_should_have_two_ctxs(self):
        self.result.contexts.should.have.length_of(2)

    def the_result_should_have_two_assertions(self):
        self.result.assertions.should.have.length_of(2)

class WhenRunningAClass(object):
    def context(self):
        class TestSpec(object):
            was_run = False
            def it(self):
                self.__class__.was_run = True
        self.spec = TestSpec

    def because_we_run_the_class(self):
        contexts.run(self.spec, contexts.core.Result())

    def it_should_run_the_test(self):
        self.spec.was_run.should.be.true

class WhenRunningAModule(object):
    def context(self):
        class HasSpecInTheName(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class HasWhenInTheName(object):
            was_run = False
            def it_should_run_this(self):
                self.__class__.was_run = True
        class NormalClass(object):
            was_instantiated = False
            def __init__(self):
                self.__class__.was_instantiated = True
        self.module = types.ModuleType('fake_specs')
        self.module.HasSpecInTheName = HasSpecInTheName
        self.module.HasWhenInTheName = HasWhenInTheName
        self.module.NormalClass = NormalClass

    def because_we_run_the_module(self):
        contexts.run(self.module, contexts.core.Result())

    def it_should_run_the_spec(self):
        self.module.HasSpecInTheName.was_run.should.be.true

    def it_should_run_the_other_spec(self):
        self.module.HasWhenInTheName.was_run.should.be.true

    def it_should_not_instantiate_the_normal_class(self):
        self.module.NormalClass.was_instantiated.should.be.false

class WhenRunningAFile(object):
    def establish_that_there_is_a_file_in_the_filesystem(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.module_name = "test_file"
        self.create_folder()
        self.write_file()

    def because_we_run_the_file(self):
        contexts.run(self.filename, contexts.core.Result())

    def it_should_import_the_file(self):
        sys.modules.should.contain(self.module_name)

    def it_should_run_the_specs(self):
        sys.modules[self.module_name].module_ran.should.be.true

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        try:
            shutil.rmtree(self.folder_path)
        finally:
            del sys.modules[self.module_name]

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), 'data')
        os.mkdir(self.folder_path)

    def write_file(self):
        self.filename = os.path.join(self.folder_path, self.module_name+".py")
        with open(self.filename, 'w+') as f:
            f.write(self.code)

class WhenRunningAFolderWhichIsNotAPackage(object):
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.module_names = ["test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_first_module(self):
        sys.modules.should.contain(self.module_names[0])

    def it_should_import_the_second_module(self):
        sys.modules.should.contain(self.module_names[1])

    def it_should_run_the_first_module(self):
        sys.modules[self.module_names[0]].module_ran.should.be.true

    def it_should_run_the_second_module(self):
        sys.modules[self.module_names[1]].module_ran.should.be.true

    def it_should_not_run_the_non_test_module(self):
        sys.modules.should_not.contain(self.module_names[2])

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        try:
            shutil.rmtree(self.folder_path)
        finally:
            del sys.modules[self.module_names[0]]
            del sys.modules[self.module_names[1]]

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), 'non_package_folder')
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n+".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)

class WhenRunningAFolderWhichIsAPackage(object):
    def establish_that_there_is_a_folder_containing_modules(self):
        self.code = """
module_ran = False

class TestSpec(object):
    def it(self):
        global module_ran
        module_ran = True
"""
        self.old_sys_dot_path = sys.path[:]
        self.package_name = 'package_folder'
        self.module_names = ["__init__", "test_file1", "test_file2", "an_innocent_module"]
        self.create_folder()
        self.write_files()

    def because_we_run_the_folder(self):
        contexts.run(self.folder_path, contexts.core.Result())

    def it_should_import_the_package(self):
        sys.modules.should.contain(self.package_name)

    def it_should_import_the_first_module(self):
        assert self.package_name + '.' + self.module_names[1] in sys.modules
        sys.modules.should.contain(self.package_name + '.' + self.module_names[1])

    def it_should_import_the_second_module(self):
        assert self.package_name + '.' + self.module_names[2] in sys.modules
        sys.modules.should.contain(self.package_name + '.' + self.module_names[2])

    def it_should_run_the_package(self):
        sys.modules[self.package_name].module_ran.should.be.true

    def it_should_run_the_first_module(self):
        sys.modules[self.package_name + '.' + self.module_names[1]].module_ran.should.be.true

    def it_should_run_the_second_module(self):
        sys.modules[self.package_name + '.' + self.module_names[2]].module_ran.should.be.true

    def it_should_not_modify_sys_dot_path(self):
        sys.path.should.equal(self.old_sys_dot_path)

    def cleanup_the_file_system_and_sys_dot_modules(self):
        try:
            shutil.rmtree(self.folder_path)
        finally:
            try:
                del sys.modules[self.package_name + '.' + self.module_names[1]]
                del sys.modules[self.package_name + '.' + self.module_names[2]]
                del sys.modules[self.package_name]
            except KeyError:
                pass

    def create_folder(self):
        this_file = os.path.realpath(__file__)
        self.folder_path = os.path.join(os.path.dirname(this_file), self.package_name)
        os.mkdir(self.folder_path)

    def write_files(self):
        self.filenames = [os.path.join(self.folder_path, n + ".py") for n in self.module_names]
        for fn in self.filenames:
            with open(fn, 'w+') as f:
                f.write(self.code)


if __name__ == "__main__":
    contexts.main()
