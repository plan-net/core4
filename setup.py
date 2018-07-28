# tests requires: coverage==4.5.1
import sys, os
from setuptools import setup, find_packages

sys.path.insert(0, os.getcwd())

import core4.util

setup(name='core4',
      version=core4.__version__,
      packages=find_packages(exclude=['docs', 'tests*', 'plugin']),
      scripts=[],
      package_data={
          '': ['*.conf'] + core4.util.package_files(
              'core4/api', ['.+\.(html|js|css|tmpl)$'])
      },
      zip_safe=False
)
