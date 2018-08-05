# tests requires: coverage==4.5.1
import os
import re
import sys
from subprocess import check_call

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import core4

with open("README.md", "r") as fh:
    long_description = fh.read()


class MyTestCommand(TestCommand):

    def run_tests(self):
        check_call([sys.executable, "tests/runner.py"])


class MySphinxCommand(TestCommand):

    def run_tests(self):
        check_call(
            ["sphinx-build", "-a", "-q", "docs/source", "docs/build/html"])
        print("\nopen core4 documentation at docs/build/html/index.html")


def package_files(directory, pattern):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            if sum([1 for p in pattern
                    if re.match(p, filename) is not None]) > 0:
                paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='core4',
    version=core4.__version__,
    author="Michael Rau",
    author_email="m.rau@plan-net.com",
    description="CORE4 delivers a unified insights platform from data "
                "integration, and information/workflow automation to "
                "web-based business applications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/m-rau/core4",
    packages=find_packages(exclude=['docs', 'tests*', 'plugin']),
    scripts=[],
    console_scripts=[],
    package_data={
        '': package_files('core4/api', ['.+\.(html|js|css|tmpl)$'])
    },
    tests_require=[
        "coverage>=4.0, <5.0",
    ],
    install_requires=[
        "numpy>=1.14, <1.15",
        "pandas>=0.22, <0.23",
        "pymongo>=3.6, <3.7",
        "python-dateutil>=2.7, <2.8",
        "Sphinx>=1.7, <1.8",
        "sphinx-rtd-theme==0.3, <0.4",
        "Flask>=1.0, <2.0",
        "Flask-Login>=0.4, <1.0"
    ],
    zip_safe=False,
    cmdclass={
        'test': MyTestCommand,
        'sphinx': MySphinxCommand
    },
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux"
    ),
)
