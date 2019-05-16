# -*- coding: utf-8 -*-

import ctypes

import core4.base.main
import core4.logger.mixin
import core4.queue.helper
import core4.queue.helper.job
import core4.queue.job
import core4.queue.main
import core4.queue.worker
import core4.util.node


LOOP_INTERVAL = 0.25
libc = ctypes.CDLL(None)

import logging
import os
import signal
import pymongo
import pytest

import core4.base
import core4.logger.mixin
import core4.service.setup
import core4.util
import core4.util.tool

ASSET_FOLDER = '../asset'
MONGO_URL = 'mongodb://core:654321@testmongo:27017'
MONGO_DATABASE = 'core4test'


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
    os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
    os.environ["CORE4_OPTION_logging__write_concern"] = "!!int 1"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"

    core4.logger.mixin.logon()
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
    # ignore signal from children to avoid defunct zombies
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture
def queue():
    return core4.queue.main.CoreQueue()


class ExceptionJob(core4.queue.job.CoreJob):
    author = "mra"

    def execute(self, *args):
        self.logger.info("STARTUP")
        self.logger.debug("STARTUP (debug)")
        if self.cookie.get("counter") is None:
            self.logger.info("setting counter to 0")
            self.cookie.set("counter", 0)
        else:
            self.logger.debug("starting job with counter [%s]",
                              self.cookie.get("counter"))
        self.cookie.inc("counter")
        if self.cookie.get("counter") > 2:
            self.logger.debug("will raise RuntimeError")
            raise RuntimeError()
        self.logger.debug("will finish successfully")
        self.logger.info("ENDUP")


def test_job_exception_logging(queue):
    job = queue.enqueue(ExceptionJob)
    worker = core4.queue.worker.CoreWorker()
    worker.at = core4.util.node.mongo_now()
    worker.work_jobs()

    def waiter(_id):
        while True:
            j = queue.config.sys.journal.find_one({"_id": _id})
            if j is not None:
                print("found state", j["state"])
                break

    waiter(job._id)

    job = queue.enqueue(ExceptionJob)
    worker.work_jobs()
    waiter(job._id)

    job = queue.enqueue(ExceptionJob)
    worker.work_jobs()

    while True:
        j = queue.config.sys.queue.find_one()
        if j["state"] == "error":
            break
    while True:
        j = queue.config.sys.log.find_one({"level": "CRITICAL"})
        if j is not None:
            break
    data = list(queue.config.sys.log.find(sort=[("epoch", 1)]))
    debugs = sum([1 for i in data if
                  i["identifier"] == str(job._id) and i["level"] == "DEBUG"])
    assert debugs == 3
