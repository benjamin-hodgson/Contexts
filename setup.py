from setuptools import setup

setup(
    name = "pyspec",
    version = "0.0.1",
    package_dir = {'':"src"},
    packages = [
        "pyspec",
    ],
    tests_require = ["sure >= 1.2.2"]
)
