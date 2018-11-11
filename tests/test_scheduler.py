import logging
import os
import re

import datetime
import pymongo
import pytest
import threading
import time

import core4.logger.mixin
import core4.queue.job
import core4.util
import core4.util.tool
from core4.queue.main import CoreQueue
from core4.queue.scheduler import CoreScheduler
from tests.test_worker import worker, mongodb, queue

# from tests.util import asset

w = worker
m = mongodb
q = queue

ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    yield
    # teardown database
    conn.drop_database(MONGO_DATABASE)
    # run @once methods
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    # singletons
    core4.util.tool.Singleton._instances = {}
    # os environment
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


class SchedulerHelper:
    def __init__(self):
        self.queue = core4.queue.main.CoreQueue()
        self.pool = None
        self.scheduler = None

    def start(self):
        self.scheduler = core4.queue.scheduler.CoreScheduler(
            name="scheduler")
        self.pool = threading.Thread(target=self.scheduler.start, args=())
        self.pool.start()

    def stop(self):
        self.scheduler.exit = True
        self.pool.join()


@pytest.fixture
def scheduler():
    return SchedulerHelper()


class InvalidSchedule(core4.queue.job.CoreJob):
    author = "mra"
    schedule = "a b c"


class ValidSchedule1(InvalidSchedule):
    author = "mra"
    schedule = "5 * * * *"


class ValidSchedule2(InvalidSchedule):
    author = "mra"
    schedule = "10 */2 * * *"


def test_init():
    s = CoreScheduler()
    s.startup()
    time.sleep(1)
    s.startup()
    assert 'tests.test_scheduler.ValidSchedule1' in s.job.keys()
    assert 'tests.test_scheduler.ValidSchedule2' in s.job.keys()
    assert 'tests.test_scheduler.ValidSchedule3' in s.job.keys()
    assert (s.job['tests.test_scheduler.ValidSchedule1']["created_at"]
            < s.job['tests.test_scheduler.ValidSchedule1']["updated_at"])


def test_timer(queue, mongodb):
    s = CoreScheduler()
    s.startup()
    s.previous = None
    s.at = datetime.datetime(2018, 1, 1, 23, 50, 0)
    n = 0
    enqueued = {}
    for i in range(60 * 60):
        n += 1
        s.run_step()
        for job in mongodb.core4test.sys.queue.find(projection=["name"]):
            enqueued.setdefault(job["name"], []).append(s.at)
        mongodb.core4test.sys.queue.delete_many({})
        s.at += datetime.timedelta(seconds=1)
    assert (sorted(enqueued['tests.test_scheduler.ValidSchedule1']) == [
        datetime.datetime(2018, 1, 2, 0, 5)])
    assert (sorted(enqueued['tests.test_scheduler.ValidSchedule2'])
            == [datetime.datetime(2018, 1, 2, 0, 10)])
    assert (sorted(enqueued['tests.test_scheduler.ValidSchedule3'])
            == [datetime.datetime(2018, 1, 2, 0, 28)])
    expected = []
    t = datetime.datetime(2018, 1, 1, 23, 51)
    for i in range(59):
        expected.append(t)
        t += datetime.timedelta(minutes=1)
    assert (sorted(enqueued['tests.test_scheduler.ValidSchedule4'])
            == expected)


def test_min_timer(queue, mongodb):
    s = CoreScheduler()
    s.startup()
    s.at = datetime.datetime(2018, 1, 1, 23, 50, 0)
    n = 0
    enqueued = {}
    for i in range(6 * 60):
        n += 1
        s.run_step()
        for job in mongodb.core4test.sys.queue.find(projection=["name"]):
            enqueued.setdefault(job["name"], []).append(s.at)
        mongodb.core4test.sys.queue.delete_many({})
        s.at += datetime.timedelta(minutes=1)
    assert len(enqueued['tests.test_scheduler.ValidSchedule1']) == 6
    assert len(enqueued['tests.test_scheduler.ValidSchedule2']) == 3
    assert len(enqueued['tests.test_scheduler.ValidSchedule3']) == 6
    assert len(enqueued['tests.test_scheduler.ValidSchedule4']) == 359


class GapJob1(core4.queue.job.CoreJob):
    author = "mra"
    schedule = "20,30,40 * * * *"


class GapJob2(core4.queue.job.CoreJob):
    author = "mra"
    schedule = "20 23 * * *"


def test_gap(mongodb):
    s = CoreScheduler()
    s.startup()
    s.at = datetime.datetime(2018, 1, 1, 0, 9, 0)
    s.run_step()
    expected = {
        "ValidSchedule1": 0,
        "ValidSchedule2": 0,
        "ValidSchedule3": 0,
        "ValidSchedule4": 0,
        "GapJob1": 0,
        "GapJob2": 0
    }
    for e, c in expected.items():
        assert mongodb.core4test.sys.queue.count_documents(
            {'name': re.compile(e)}) == c
    s.at = datetime.datetime(2018, 1, 1, 0, 10, 30)
    s.run_step()
    expected = {
        "ValidSchedule1": 0,
        "ValidSchedule2": 1,
        "ValidSchedule3": 0,
        "ValidSchedule4": 1,
        "GapJob1": 0,
        "GapJob2": 0
    }
    for e, c in expected.items():
        assert mongodb.core4test.sys.queue.count_documents(
            {'name': re.compile(e)}) == c
    s.at = datetime.datetime(2018, 1, 1, 23, 19, 0)
    s.run_step()
    expected = {
        "ValidSchedule1": 1,
        "ValidSchedule2": 1,
        "ValidSchedule3": 1,
        "ValidSchedule4": 1,
        "GapJob1": 1,
        "GapJob2": 0
    }
    for e, c in expected.items():
        assert mongodb.core4test.sys.queue.count_documents(
            {'name': re.compile(e)}) == c
    s.at = datetime.datetime(2018, 1, 2, 23, 0, 0)
    s.run_step()
    expected = {
        "ValidSchedule1": 1,
        "ValidSchedule2": 1,
        "ValidSchedule3": 1,
        "ValidSchedule4": 1,
        "GapJob1": 1,
        "GapJob2": 1
    }
    for e, c in expected.items():
        assert mongodb.core4test.sys.queue.count_documents(
            {'name': re.compile(e)}) == c


class ValidSchedule3(InvalidSchedule):
    author = "mra"
    schedule = "28 * * * *"


class ValidSchedule4(InvalidSchedule):
    author = "mra"
    schedule = "* * * * *"


@pytest.mark.timeout(30)
def test_loop(queue, scheduler):
    scheduler.start()
    while sum([1 for w in queue.get_worker()
               if w["loop_time"] is not None]) < 1:
        time.sleep(0.5)
    while scheduler.scheduler.cycle["total"] < 3:
        time.sleep(0.5)
    scheduler.stop()
    while sum([1 for w in queue.get_worker()
               if w["phase"]["shutdown"] is not None]) > 0:
        time.sleep(0.5)
