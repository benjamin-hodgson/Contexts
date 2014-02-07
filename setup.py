import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages


builtin_plugins = [
    'TestObjectSupplier = contexts.plugins.object_supplier:TestObjectSupplier',
    'ExitCodeReporter = contexts.plugins.shared:ExitCodeReporter',
    'Shuffler = contexts.plugins.shuffling:Shuffler',
    'Importer = contexts.plugins.importing:Importer',
    'AssertionRewritingImporter = contexts.plugins.assertion_rewriting:AssertionRewritingImporter',
    'DecoratorBasedIdentifier = contexts.plugins.decorators:DecoratorBasedIdentifier',
    'NameBasedIdentifier = contexts.plugins.name_based_identifier:NameBasedIdentifier',
    'TeamCityReporter = contexts.plugins.teamcity:TeamCityReporter',
    'DotsReporter = contexts.plugins.cli:DotsReporter',
    'VerboseReporter = contexts.plugins.cli:VerboseReporter',
    'StdOutCapturingReporter = contexts.plugins.cli:StdOutCapturingReporter',
    'Colouriser = contexts.plugins.cli:Colouriser', 'UnColouriser = contexts.plugins.cli:UnColouriser',
    'FailuresOnlyMaster = contexts.plugins.cli:FailuresOnlyMaster',
    'FailuresOnlyBefore = contexts.plugins.cli:FailuresOnlyBefore',
    'FailuresOnlyAfter = contexts.plugins.cli:FailuresOnlyAfter',
    'FinalCountsReporter = contexts.plugins.cli:FinalCountsReporter',
    'TimedReporter = contexts.plugins.cli:TimedReporter',
]


setup(
    name = "Contexts",
    version = "0.8.1",
    author = "Benjamin Hodgson",
    author_email = "benjamin.hodgson@huddle.net",
    url = "https://github.com/benjamin-hodgson/Contexts",
    description = """Dead simple descriptive testing for Python. No custom decorators, no context managers, no '.feature' files, no fuss.""",
    long_description = """See the Github project page (https://github.com/benjamin-hodgson/Contexts) for more information.""",
    package_dir = {'':'src'},
    packages = find_packages('src'),
    install_requires = ["setuptools >= 1.0"],
    extras_require = {'colour': ["colorama >= 0.2.7"]},
    entry_points = {
    	'console_scripts': ['run-contexts = contexts.__main__:cmd'],
        'contexts.plugins': builtin_plugins,
    }
)
