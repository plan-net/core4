# -*- coding: utf-8 -*-

import os
import re
from subprocess import check_call

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import core4

with open("README.md", "r") as fh:
    long_description = fh.read()


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
    setup_requires=[
    ],
    entry_points={
        'console_scripts': [
            'coco=core4.script.coco:main'
        ],
    },
    install_requires=[
        "pymongo>=3.7",
        "python-dateutil>=2.7",
        "Flask>=1.0",
        "Flask-Login>=0.4",
        "PyYaml>=3.12",
        "psutil>=5.4",
        "docopt>=0.6"
    ],
    extras_require={
        "tests": [
            "pytest",
            "pytest-timeout",
            "pytest-runner",
            "requests",
            "coverage",
            "Sphinx",
            "sphinx-rtd-theme"
        ]
    },
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
