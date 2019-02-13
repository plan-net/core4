import logging
import os
import re
from pprint import pprint

import bson.objectid
import datetime
import pymongo
import pytest

import core4.base
import core4.config.test
import core4.logger.mixin
import core4.queue.helper.functool
import core4.queue.helper.job.base
import core4.queue.job
import core4.service.setup
from core4.queue.helper.functool import execute

ASSET_FOLDER = '../asset'
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
    core4.service.setup.CoreSetup().make_all()
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


class LoadJob(core4.queue.helper.job.base.CoreLoadJob):
    author = "mra"

    def execute(self, *args):
        pass


def touch(*filename):
    fullname = os.path.join(*filename)
    dirname = os.path.dirname(fullname)
    os.makedirs(dirname, exist_ok=True)
    with open(fullname, "w", encoding="utf-8") as fh:
        fh.write("")


def test_list_files():
    job = LoadJob()
    transfer = job.config.get_folder("transfer")
    touch(transfer, "tests/test1.txt")
    touch(transfer, "tests/test2.txt")
    touch(transfer, "tests/test3.txt")
    data = job._list_files("transfer")
    assert len(data) == 3
    data = job._list_files("transfer", ".+\.txt$")
    assert len(data) == 3
    data = job._list_files("transfer", ".+3.+")
    assert len(data) == 1
    data = job._list_files("transfer", re.compile(".+3.+"))
    assert len(data) == 1
    data = job.list_transfer()
    assert len(data) == 3
    data = job.list_transfer(".+\.txt$")
    assert len(data) == 3
    data = job.list_transfer(".+3.+")
    assert len(data) == 1
    data = job.list_transfer(re.compile(".+3.+"))
    assert len(data) == 1


def test_base_folder():
    job = LoadJob()
    transfer = job.config.get_folder("transfer")
    fn = "base/test3.txt"
    touch(transfer, fn)
    assert job.list_transfer() == []
    data = job.list_transfer(base="base")
    assert len(data) == 1
    f = os.path.join(transfer, fn)
    assert data[0] == f


def test_file_maker():
    job = LoadJob()
    fn = job._make_file("transfer", "bla/test.txt")
    open(fn, "w", encoding="utf-8").write("")
    fn = job._make_file("transfer")
    open(fn, "w", encoding="utf-8").write("")


def test_move():
    job = LoadJob()
    transfer = job.config.get_folder("transfer")
    fn = "tests/test1.txt"
    touch(transfer, fn)
    data = job.list_transfer(".+\.txt$")
    job.move_proc(data[0])
    data = job.list_proc(".+\.txt$")
    assert data[0].endswith("/proc/tests/test1.txt")


def test_archive():
    job = LoadJob()
    transfer = job.config.get_folder("transfer")
    fn = "tests/test1.txt"
    touch(transfer, fn)
    data = job.list_transfer(".+\.txt$")
    job.move_proc(data[0])
    data = job.list_proc(".+\.txt$")
    with pytest.raises(RuntimeError):
        job.move_archive(data[0])
    job.__dict__["started_at"] = datetime.datetime(2018, 1, 2, 3, 4, 5)
    with pytest.raises(RuntimeError):
        job.move_archive(data[0])
    job.__dict__["_id"] = bson.objectid.ObjectId()
    job.move_archive(data[0], compress=False)
    archive = transfer = job.config.get_folder("archive")
    target = os.path.join(archive, "tests/2018/01/02/" + str(job._id)
                          + "/test1.txt")
    assert os.path.exists(target)
    assert os.path.isfile(target)


def test_archive_compress():
    job = LoadJob()
    transfer = job.config.get_folder("transfer")
    fn = "tests/test1.txt"
    touch(transfer, fn)
    data = job.list_transfer(".+\.txt$")
    job.move_proc(data[0])
    data = job.list_proc(".+\.txt$")
    with pytest.raises(RuntimeError):
        job.move_archive(data[0])
    job.__dict__["started_at"] = datetime.datetime(2018, 1, 2, 3, 4, 5)
    with pytest.raises(RuntimeError):
        job.move_archive(data[0])
    job.__dict__["_id"] = bson.objectid.ObjectId()
    job.move_archive(data[0])
    archive = transfer = job.config.get_folder("archive")
    target = os.path.join(archive, "tests/2018/01/02/" + str(job._id)
                          + "/test1.txt.gz")
    assert os.path.exists(target)
    assert os.path.isfile(target)


class Job1(core4.queue.job.CoreJob):
    author = "mra"

    def execute(self):
        config = self.config
        coll = config.tests.test_collection
        coll.insert_one({"hello": "world"})

    def _make_config(self, *args, **kwargs):
        kwargs["project_name"] = "tests"
        kwargs["project_dict"] = {
            "test_collection": core4.config.tag.ConnectTag(
                "mongodb://test_collection"),
            "test_collection2": core4.config.tag.ConnectTag(
                "mongodb://test_collection2")
        }
        kwargs["local_dict"] = {
            "DEFAULT": {
                "mongo_url": MONGO_URL,
                "mongo_database": MONGO_DATABASE,
            },
            "logging": {
                "mongodb": "DEBUG"
            }
        }
        return core4.config.test.TestConfig(*args, **kwargs)


def test_nojob_collection():
    ret = execute(Job1)
    assert ret["last_error"]["exception"].startswith(
        """AttributeError('_id and _src must not be None"""
    )
    assert ret["state"] == "error"


class Job2(Job1):
    author = "mra"

    def execute(self):
        config = self.config
        coll = config.tests.test_collection
        self.set_source("dirname/test.txt")
        coll.insert_one({"hello": "world"})
        data = []
        for doc in coll.find():
            data.append(doc)
        assert len(data) == 1
        assert data[0]["_job_id"] == self._id
        assert data[0]["_src"] == "test.txt"

        coll.insert_many([
            {"hello": 1},
            {"hello": 2},
        ])
        from pymongo import InsertOne, DeleteOne, ReplaceOne
        requests = [InsertOne({'hello': 3}), DeleteOne({'x': 1}),
                    ReplaceOne({'hello': 1}, {'hello': 1.234}, upsert=True)]
        coll.bulk_write(requests)

        requests = [InsertOne({'hello': 4}), DeleteOne({'x': 1}),
                    ReplaceOne({'hello': 1.234}, {'zz': 1}, upsert=True)]
        coll.bulk_write(requests)
        coll.update_one({"hello": 5}, {"$set": {"ua": 1}}, upsert=True)
        coll.update_many({"hello": "5"}, {"$set": {"ua": 2}}, upsert=True)
        data = []
        for doc in coll.find():
            data.append(doc)
        assert len(data) == 7
        assert set([d["_job_id"] for d in data]) == {self._id}
        assert set([d["_src"] for d in data]) == {"test.txt"}


def test_job_collection():
    ret = execute(Job2)
    assert ret["state"] == "complete"


class Job3(Job1):
    author = "mra"

    def execute(self):
        config = self.config
        coll = config.tests.test_collection
        self.set_source("dirname1/test1.txt")
        coll.insert_one({"hello": "document 1", "source": "test1.txt"})
        coll.insert_one({"hello": "document 2", "source": "test1.txt"})
        self.set_source("dirname2/test2.txt")
        self.set_source("dirname1/test1.txt")
        self.set_source("dirname2/test2.txt")
        coll.insert_one({"hello": "document 3", "source": "test2.txt"})
        coll.insert_one({"hello": "document 4", "source": "test2.txt"})


def test_multi_source():
    ret = execute(Job3)
    assert ret["state"] == "complete"
    base = Job3()
    coll = base.config.tests.test_collection
    for doc in coll.find():
        assert doc["source"] == doc["_src"]
        assert doc["_job_id"] == ret["_id"]
    assert sorted(ret["sources"]) == ['test1.txt', 'test2.txt']

class Job4(Job1):
    author = "mra"

    def execute(self):
        config = self.config
        coll = config.tests.test_collection
        self.set_source("dirname1/test1.txt")
        for i in range(1000):
            config.tests.test_collection.insert_one({"hello": "document 1", "source": "test1.txt"})

        syscoll = self.config.sys.log
        syscoll.insert_one({})
        print(syscoll.count_documents({}))
        self.set_source("dirname2/test2.txt")
        coll2 = config.tests.test_collection2
        coll2.insert_one({"hello": "document 3", "source": "test2.txt"})
        coll2.insert_one({"hello": "document 4", "source": "test2.txt"})
        coll.insert_one({"hello": "document 5", "source": "test2.txt"})

def test_change_source():
    ret = execute(Job4)
    assert ret["state"] == "complete"
    base = Job4()
    coll = base.config.tests.test_collection
    for doc in coll.find():
        assert doc["source"] == doc["_src"]
