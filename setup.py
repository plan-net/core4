from setuptools import find_packages, setup
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
            'chist=core4.script.chist:main'
        ],
    },
    python_requires='>=3.8',
    install_requires=[
        "wheel>=0.32.3",
        "pymongo<4,>=3.12",
        "python-dateutil>=2.7",
        "PyYaml>=3.12",
        "psutil>=5.4",
        "docopt>=0.6",
        "croniter>=0.3",
        "python-mimeparse>=1.6",
        "PyJWT>=2.0.0a",
        # see https://github.com/jpadilla/pyjwt/issues/391#issuecomment-515427821
        "tornado>=5.1,<6.3",
        # "pandas>=2.0.3", installed with alpine on docker
        "motor==2.5.1",
        "passlib>=1.7",
        "python-magic>=0.4",
        "docutils==0.16",
        "Sphinx>=1.8.2,<6",
        "sh>=1.12.14",
        "pip>=18.1",
        "pytz>=2018.9",
        "tzlocal>=1.5.1",
        "feather-format==0.4.0",
        "cffi",
        "rpy2==3.0.5",
        "pql @ git+https://github.com/comfuture/pql.git"
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
    zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux"
    )
)
