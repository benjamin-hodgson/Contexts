from contexts.plugins import reporting


class WhenMakingANameHumanReadable:
    @classmethod
    def examples(self):
        yield "lowercase", "lowercase"
        yield "Capitalised", "Capitalised"
        yield "snake_case_name", "snake case name"
        yield "Camel_Snake_Case", "Camel snake case"
        yield "CamelCase", "Camel case"
        yield "HTML", "HTML"
        yield "HTMLParser", "HTML parser"
        yield "SimpleHTTPServer", "Simple HTTP server"
        yield "November2013", "November 2013"
        yield "ABC123", "ABC 123"
        yield "BMW4Series", "BMW 4 series"
        yield "lowerAtStart", "lower at start"
        yield "has.dots.in.the.name", "has dots in the name"
        yield "CamelCaseWithASingleLetterWord", "Camel case with a single letter word"
        yield "Does.EverythingAT_once.TOBe100Percent_Certain", "Does everything AT once TO be 100 percent certain"

    def because_we_make_the_string_readable(self, input, expected):
        self.result = reporting.make_readable(input)

    def it_should_return_a_string_with_appropriate_spaces(self, input, expected):
        assert self.result == expected


class WhenGettingExitCodeForASuccessfulRun:
    def in_the_context_of_a_successful_run(self):
        self.plugin = reporting.ExitCodeReporter()

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_0(self):
        assert self.result == 0


class WhenGettingExitCodeAfterAnAssertionFailure:
    def establish_that_an_assertion_failed(self):
        self.plugin = reporting.ExitCodeReporter()
        self.plugin.assertion_failed(lambda: None, Exception())

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_1(self):
        assert self.result == 1


class WhenGettingExitCodeAfterAnAssertionError:
    def establish_that_an_assertion_errored(self):
        self.plugin = reporting.ExitCodeReporter()
        self.plugin.assertion_errored(lambda: None, Exception())

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_1(self):
        assert self.result == 1


class WhenGettingExitCodeAfterAContextError:
    def establish_that_a_context_errored(self):
        self.plugin = reporting.ExitCodeReporter()
        self.plugin.context_errored('', None, Exception())

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_1(self):
        assert self.result == 1


class WhenGettingExitCodeAfterATestClassError:
    def establish_that_a_context_errored(self):
        self.plugin = reporting.ExitCodeReporter()
        self.plugin.test_class_errored(type('',(),{}), Exception())

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_1(self):
        assert self.result == 1


class WhenGettingExitCodeAfterAnUnexpectedError:
    def establish_that_a_context_errored(self):
        self.plugin = reporting.ExitCodeReporter()
        self.plugin.unexpected_error(Exception())

    def because_we_ask_for_the_exit_code(self):
        self.result = self.plugin.get_exit_code()

    def it_should_return_1(self):
        assert self.result == 1
