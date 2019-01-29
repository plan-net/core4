import logging
import os

import pytest
import pymongo
import pymongo.errors
import core4.logger.mixin
import core4.service.setup
import core4.util.tool
from core4.api.v1.request.role.model import CoreRole
import core4.service.access.manager


curr_dir = os.path.abspath(os.curdir)

ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


def has_access(username, token, database):
    url = "mongodb://" + username + ':' + token + '@' + "localhost:27017"
    mongo = pymongo.MongoClient(url)
    return mongo[database]

@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_sys__userdb"] = "test_user_db!"
    core4.logger.mixin.logon()
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    for db in conn.list_database_names():
        if db.startswith("test_user_db!"):
            conn.drop_database(db)
    yield conn
    # teardown database
    conn.drop_database(MONGO_DATABASE)
    for db in conn.list_database_names():
        if db.startswith("test_user_db!"):
            conn.drop_database(db)
    os.chdir(curr_dir)
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


def test_it():
    from tornado.ioloop import IOLoop
    role = CoreRole(
        name="mra",
        email="m.rau@plan-net.com",
        password="secret",
        perm=["mongodb://core4test", "mongodb://core3"]
    )
    out = IOLoop.current().run_sync(lambda: role.save())
    assert out
    role = CoreRole(
        name="mbr",
        email="test@plan-net.com",
        password="secret",
        perm=["mongodb://core3"]
    )
    out = IOLoop.current().run_sync(lambda: role.save())
    assert out
    out = IOLoop.current().run_sync(lambda: role.load_one(name="mra"))
    assert out["name"] == "mra"
    out = IOLoop.current().run_sync(lambda: role.find_one(name="mra"))
    assert out.name == "mra"
    manager = core4.service.access.manager.CoreAccessManager("mra")
    token_mra = manager.synchronise()
    db = has_access("mra", token_mra["mongodb"], "core4test")
    assert db.sys.role.count_documents({}) == 2
    manager = core4.service.access.manager.CoreAccessManager("mbr")
    token_mbr = manager.synchronise()
    db = has_access("mbr", token_mbr["mongodb"], "core4test")
    with pytest.raises(pymongo.errors.OperationFailure):
        print(db.sys.role.count_documents({}))
    db = has_access("mbr", token_mbr["mongodb"], "test_user_db!mbr")
    db.test1.insert_one({"hello": "world"})
    assert db.test1.count_documents({}) == 1
    db = has_access("mra", token_mbr["mongodb"], "test_user_db!mbr")
    with pytest.raises(pymongo.errors.OperationFailure):
        print(db.test1.count_documents({}))
