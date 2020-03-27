try:
    from pip._internal.cli.main import main
except:
    from pip import main
main(["install", "--quiet", "/home/mra/PycharmProjects/core4build"])
from core4build import setup

from setuptools import find_packages

import core4


setup(
    name='core4',
    version=core4.__version__,
    author="Michael Rau",
    author_email="Plan.Net Business Intelligence",
    description="core4os delivers a unified insights platform from data "
                "integration, and information/workflow automation to "
                "web-based business applications.",
    url="https://github.com/plan-net/core4",
    packages=find_packages(exclude=['docs', 'tests*', 'project*', 'example*',
                                    'other*']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'coco=core4.script.coco:main',
            'chist=core4.script.chist:main',
            'cadmin=core4.script.cadmin:main'
        ],
    },
    install_requires=[
        "wheel>=0.32.3",
        "pymongo>=3.7",
        "python-dateutil>=2.7",
        "PyYaml>=3.12",
        "psutil>=5.4",
        "docopt>=0.6",
        "croniter>=0.3",
        "python-mimeparse>=1.6",
        "PyJWT>=1.6",
        "tornado>=5.1",
        "pandas>=0.23",
        "motor>=2.0",
        "passlib>=1.7",
        "python-magic>=0.4",
        "docutils>=0.14",
        "Sphinx>=1.8.2",
        "sh>=1.12.14",
        "pip>=18.1",
        "pytz>=2018.9",
        "tzlocal>=1.5.1",
        "feather-format==0.4.0",
        "rpy2==3.0.5"
    ],
    extras_require={
        "tests": [
            "pytest",
            "pytest-timeout",
            "pytest-runner",
            "pytest-tornasync",
            "requests",
            "coverage",
            "sphinx-rtd-theme",
            "websockets"
        ]
    },
    #zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux"
    )
)
