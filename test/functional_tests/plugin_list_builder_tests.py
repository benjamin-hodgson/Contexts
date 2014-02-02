from contexts import catch
from contexts.plugins.decorators import action
from contexts.plugin_discovery import PluginListBuilder


class PluginListBuilderSharedContext:
    def shared_context(self):
        self.builder = PluginListBuilder()


class WhenTheListBuilderIsEmpty(PluginListBuilderSharedContext):
    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_return_an_empty_list(self):
        assert self.result == []

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenAddingAFewPluginsWhichAreNotPicky(PluginListBuilderSharedContext):
    def context(self):
        class NotDefiningLocate(object):
            pass
        class ReturningNoneFromLocate(object):
            @classmethod
            def locate(cls):
                return None
        class ReturningNoneNoneFromLocate(object):
            @classmethod
            def locate(cls):
                return (None, None)
        self.class1 = NotDefiningLocate
        self.class2 = ReturningNoneFromLocate
        self.class3 = ReturningNoneNoneFromLocate

        self.builder.add(self.class1)
        self.builder.add(self.class2)
        self.builder.add(self.class3)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_return_the_plugins(self):
        assert set(self.result) == {self.class1, self.class2, self.class3}

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenAPluginAsksToBeBeforeAPluginWhichNeverGetsAdded(PluginListBuilderSharedContext):
    def given_that_the_plugin_refers_to_a_class_we_never_added(self):
        class Plugin1(object):
            @classmethod
            def locate(cls):
                return (None, Plugin2)
        class Plugin2(object):
            pass
        self.class1 = Plugin1
        self.builder.add(self.class1)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_return_only_the_plugin_we_added(self):
        assert self.result == [self.class1]

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result

class WhenAPluginAsksToBeAfterAPluginWhichNeverGetsAdded(PluginListBuilderSharedContext):
    def given_that_the_plugin_refers_to_a_class_we_never_added(self):
        class Plugin1(object):
            @classmethod
            def locate(cls):
                return (Plugin2, None)
        class Plugin2(object):
            pass
        self.class1 = Plugin1
        self.builder.add(self.class1)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_return_only_the_plugin_we_added(self):
        assert self.result == [self.class1]

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenAPluginAsksToBeBeforeAPluginThatDoesntMind(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_that_want_to_be_first(self):
        class Plugin1(object):
            @classmethod
            def locate(cls):
                return (None, Plugin2)
        class Plugin2(object):
            pass

        yield Plugin1, Plugin2, [Plugin1, Plugin2]
        yield Plugin2, Plugin1, [Plugin1, Plugin2]

    def context(self, first, second, expected):
        self.builder.add(first)
        self.builder.add(second)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_put_the_picky_one_first(self, first, second, expected):
        assert self.result == expected

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result

class WhenAPluginAsksToBeAfterAPluginThatDoesntMind(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_that_want_to_be_first(self):
        class Plugin1(object):
            @classmethod
            def locate(cls):
                return (Plugin2, None)
        class Plugin2(object):
            pass

        yield Plugin1, Plugin2, [Plugin2, Plugin1]
        yield Plugin2, Plugin1, [Plugin2, Plugin1]

    def context(self, first, second, expected):
        self.builder.add(first)
        self.builder.add(second)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_put_the_picky_one_second(self, first, second, expected):
        assert self.result == expected

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenAPluginWantsToBeBetweenTwoOtherPlugins(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_that_want_to_be_in_the_middle(self):
        class Middle(object):
            @classmethod
            def locate(cls):
                return (Left, Right)
        class Left(object):
            pass
        class Right(object):
            pass

        yield Left, Middle, Right, [Left, Middle, Right]
        yield Left, Right, Middle, [Left, Middle, Right]
        yield Middle, Left, Right, [Left, Middle, Right]
        yield Middle, Right, Left, [Left, Middle, Right]
        yield Right, Left, Middle, [Left, Middle, Right]
        yield Right, Middle, Left, [Left, Middle, Right]

    def context(self, first, second, third, expected):
        self.builder.add(first)
        self.builder.add(second)
        self.builder.add(third)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_put_the_picky_one_second(self, first, second, third, expected):
        assert self.result == expected

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenTwoPluginsWantToBeEitherSideOfTheSamePlugin(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_that_want_to_be_in_the_middle(cls):
        class Middle(object):
            pass
        class Left(object):
            @classmethod
            def locate(cls):
                return (None, Middle)
        class Right(object):
            @classmethod
            def locate(cls):
                return (Middle, None)

        yield Left, Middle, Right, [Left, Middle, Right]
        yield Left, Right, Middle, [Left, Middle, Right]
        yield Middle, Left, Right, [Left, Middle, Right]
        yield Middle, Right, Left, [Left, Middle, Right]
        yield Right, Left, Middle, [Left, Middle, Right]
        yield Right, Middle, Left, [Left, Middle, Right]

    def context(self, first, second, third, expected):
        self.builder.add(first)
        self.builder.add(second)
        self.builder.add(third)

    def because_we_flatten_the_list(self):
        self.result = self.builder.to_list()

    def it_should_put_the_picky_one_second(self, first, second, third, expected):
        assert self.result == expected

    def the_operation_should_be_idempotent(self):
        assert self.builder.to_list() == self.result


class WhenAddingTheSamePluginTwice(PluginListBuilderSharedContext):
    def establish_that_the_plugin_is_already_there(self):
        self.plugin = type("Plugin", (), {})
        self.builder.add(self.plugin)

    @action
    def because_we_try_to_add_it_again(self):
        self.exception = catch(self.builder.add, self.plugin)

    def it_should_raise_a_ValueError(self):
        assert isinstance(self.exception, ValueError)


class WhenAPluginWantsToBeBeforeItself(PluginListBuilderSharedContext):
    def establish_that_the_plugin_is_stupid(self):
        class IAmStupid(object):
            @classmethod
            def locate(cls):
                return (IAmStupid, None)
        self.builder.add(IAmStupid)

    def because_we_try_to_flatten_the_list(self):
        self.exception = catch(self.builder.to_list)

    def it_should_raise_a_ValueError(self):
        assert isinstance(self.exception, ValueError)

class WhenAPluginWantsToBeAfterItself(PluginListBuilderSharedContext):
    def establish_that_the_plugin_is_stupid(self):
        class IAmStupid(object):
            @classmethod
            def locate(cls):
                return (None, IAmStupid)
        self.builder.add(IAmStupid)

    def because_we_try_to_flatten_the_list(self):
        self.exception = catch(self.builder.to_list)

    def it_should_raise_a_ValueError(self):
        assert isinstance(self.exception, ValueError)


class WhenTwoPluginsWantToBeBeforeEachOther(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_like_arguing_siblings(cls):
        class IWantIt(object):
            @classmethod
            def locate(cls):
                return (None, NoIWantIt)
        class NoIWantIt(object):
            @classmethod
            def locate(cls):
                return (None, NoIWantIt)

        yield IWantIt, NoIWantIt
        yield NoIWantIt, IWantIt

    def context(self, first, second):
        self.builder.add(first)
        self.builder.add(second)

    def because_we_try_to_flatten_the_list(self):
        self.exception = catch(self.builder.to_list)

    def it_should_raise_a_ValueError(self):
        assert isinstance(self.exception, ValueError)

class WhenTwoPluginsWantToBeAfterEachOther(PluginListBuilderSharedContext):
    @classmethod
    def examples_of_plugins_like_arguing_siblings(cls):
        class IWantIt(object):
            @classmethod
            def locate(cls):
                return (NoIWantIt, None)
        class NoIWantIt(object):
            @classmethod
            def locate(cls):
                return (NoIWantIt, None)

        yield IWantIt, NoIWantIt
        yield NoIWantIt, IWantIt

    def context(self, first, second):
        self.builder.add(first)
        self.builder.add(second)

    def because_we_try_to_flatten_the_list(self):
        self.exception = catch(self.builder.to_list)

    def it_should_raise_a_ValueError(self):
        assert isinstance(self.exception, ValueError)

