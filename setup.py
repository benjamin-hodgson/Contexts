import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "Contexts",
    version = "0.3.1",
    author = "Benjamin Hodgson",
    author_email = "benjamin.hodgson@huddle.net",
    url = "https://github.com/benjamin-hodgson/Contexts",
    description = """Dead simple descriptive testing for Python. No custom decorators, no context managers, no '.feature' files, no fuss.""",
    long_description = """See the Github project page (https://github.com/benjamin-hodgson/Contexts) for more information.""",
    package_dir = {'':'src'},
    packages = find_packages('src'),
    install_requires = ["setuptools >= 1.0"],
    tests_require = ["sure >= 1.2.2"],
    entry_points = {
    	'console_scripts': ['run-contexts = contexts.__main__:cmd']
    }
)
