# -*- coding: utf-8 -*-

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
            if re.search(pattern, filename):
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
    packages=find_packages(exclude=['docs', 'tests*', 'project']),
    package_data={
        '':
            ["core4.yaml"]
            + package_files("core4/service/project/template/", "^.+$")
    },
    tests_require=[
        "pytest",
        "coverage>=4.0, <5.0",
    ],
    setup_requires=[
        "pytest-runner"
    ],
    entry_points={
        'console_scripts': [
            'coco=core4.script.coco:main'
        ],
    },
    install_requires=[
        "numpy>=1.14, <1.15",
        "pandas>=0.22, <0.23",
        "pymongo>=3.6, <3.7",
        "python-dateutil>=2.7, <2.8",
        "Sphinx>=1.7, <1.8",
        "sphinx-rtd-theme==0.3, <0.4",
        "Flask>=1.0, <2.0",
        "Flask-Login>=0.4, <1.0",
        "PyYaml>=3.12, <4",
        "PyJWT>=1.6.4, <2",
        "psutil>=5.4.7",
        "docopt>=0.6.1"
    ],
    zip_safe=False,
    cmdclass={
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
