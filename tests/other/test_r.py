from _pytest import logging

from core4.queue.helper.job.r import CoreRJob
import pandas as pd
import pandas.errors as pd_err
import os
import pymongo
import pytest
import core4.base
import core4.config.test
import core4.logger.mixin
import core4.queue.helper.functool
import core4.queue.helper.job.base
import core4.queue.job
import core4.service.setup
import logging
import signal
import core4.base
import core4.logger.mixin
import core4.service.setup
import core4.util
import core4.util.tool


from core4.queue.main import CoreQueue
from tests.be.test_worker import WorkerHelper

ASSET_FOLDER = '../asset'
MONGO_URL = 'mongodb://core:654321@testmongo:27017'
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
    # ignore signal from children to avoid defunct zombies
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)

class MyTestRJob(CoreRJob):
    author = 'lst'


    def execute(self):
        result = self.r(source="r_test.R")
        if result is pd.DataFrame.empty:
            raise pd_err.EmptyDataError


@pytest.fixture
def worker():
    return WorkerHelper()

@pytest.mark.timeout(300)
def test_RJob(worker):
    queue = CoreQueue()
    job = MyTestRJob
    queue.enqueue(job)
    worker.start(1)
    worker.wait_queue()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if
                "done execution with [complete]" in d["message"]]) == 1
    # counter = 0
    # while counter < 60:
    #     if state == "complete":
    #         pytest.exit(returncode=0)
    #     time.sleep(5)
    #     queue.find_job(job_id)
    #     state = job.state
    #     counter += 1



