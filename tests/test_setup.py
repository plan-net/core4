# -*- coding: utf-8 -*-

import core4.base
import core4.logger.mixin
import core4.service.setup
import core4.util
from tests.pytest_util import *


def test_make_folder():
    setup = core4.service.setup.CoreSetup()
    setup.make_folder()
    for f in ["transfer", "proc", "arch", "temp"]:
        assert os.path.exists(os.path.join(setup.config.folder.root, f))


def test_make_queue2():
    setup = core4.service.setup.CoreSetup()
    setup.make_folder()
    for f in ["transfer", "proc", "arch", "temp"]:
        assert os.path.exists(os.path.join(setup.config.folder.root, f))


def test_register_jobs():
    setup = core4.service.setup.CoreSetup()
    from pprint import pprint
    pprint(setup.collect_jobs())
