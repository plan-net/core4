# -*- coding: utf-8 -*-

import logging
import os

import pymongo
import pytest

import core4.base
import core4.base.collection
import core4.config
import core4.config.tag
import core4.error
import core4.error
import core4.queue.helper
import core4.queue.helper.job
import core4.queue.job
import core4.queue.main
import core4.service.setup

ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)


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
    os.environ["CORE4_OPTION_logging__write_concern"] = "!!int 1"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"

    class LogOn(core4.base.CoreBase,
                core4.logger.mixin.CoreLoggerMixin):
        pass

    logon = LogOn()
    logon.setup_logging()
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    yield conn
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


def test_job_found():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.helper.job.DummyJob)


def test_job_not_found():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(core4.error.CoreJobNotFound):
        q.enqueue("DummyJob")


def test_no_class():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(TypeError):
        q.enqueue(pytest)


def test_no_module():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(ImportError):
        q.enqueue("notfound.job")


def test_no_module2():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(ImportError):
        q.enqueue("123notfound.job")
    with pytest.raises(ImportError):
        q.enqueue("123 notfound.job")


def test_no_mro():
    q = core4.queue.main.CoreQueue()

    class T:
        def __init__(self, *args, **kwargs):
            pass

    with pytest.raises(TypeError):
        q.enqueue(T())


def test_no_mro2():
    q = core4.queue.main.CoreQueue()

    class Test: pass

    with pytest.raises(TypeError):
        q.enqueue(Test())


def test_no_mro3():
    q = core4.queue.main.CoreQueue()

    class Test: pass

    with pytest.raises(TypeError):
        q.enqueue(Test)


def test_enqueue():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.helper.job.DummyJob)


def test_enqueue_args():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.helper.job.DummyJob, a1=1, a2=2, a3=3)
    with pytest.raises(core4.error.CoreJobExists):
        q.enqueue(core4.queue.helper.job.DummyJob,
                  args={"a1": 1, "a2": 2, "a3": 3})
    q.enqueue(core4.queue.helper.job.DummyJob)
    with pytest.raises(core4.error.CoreJobExists):
        q.enqueue(core4.queue.helper.job.DummyJob)


def test_invalid():
    q = core4.queue.main.CoreQueue()

    class T1(core4.queue.job.CoreJob): pass

    with pytest.raises(AssertionError):
        q.enqueue(T1)

    class T2(core4.queue.job.CoreJob):
        author = 'mra'

    q.enqueue(T2)


def test_project_maintenance():
    q = core4.queue.main.CoreQueue()
    assert not q.maintenance('project')
    q.enter_maintenance('project')
    q.enter_maintenance('project1')
    q.leave_maintenance('XXX')
    assert q.maintenance('project')
    assert q.maintenance('project1')
    q.leave_maintenance('project')
    assert q.maintenance('project1')
    assert not q.maintenance('project')
    q.leave_maintenance('project1')
    assert not q.maintenance('project1')


