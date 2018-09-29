# -*- coding: utf-8 -*-

import time
from threading import Thread

import core4.base.main
import core4.logger.mixin
import core4.queue.worker
from tests.pytest_util import *


@pytest.fixture(autouse=True)
def worker_timing():
    os.environ["CORE4_OPTION_worker__execution_plan__work_jobs"] = "!!int 1"


def test_plan():
    worker = core4.queue.worker.CoreWorker()
    assert len(worker.create_plan()) == 6


def test_5loops():
    worker = core4.queue.worker.CoreWorker()
    t = Thread(target=worker.start, args=())
    t.start()
    while worker.cycle_no < 5:
        time.sleep(0.5)
    worker.exit = True
    t.join()


def test_setup():
    worker = core4.queue.worker.CoreWorker()
    worker.exit = True
    worker.start()
