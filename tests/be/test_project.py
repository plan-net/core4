import logging
import os

import pymongo
import pytest

import core4.logger.mixin
from core4.service.introspect import CoreIntrospector


MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'
ASSET_FOLDER = '../asset'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture(autouse=True)
def setup(tmpdir):
    logging.shutdown()
    core4.logger.mixin.CoreLoggerMixin.completed = False
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    yield
    conn.drop_database(MONGO_DATABASE)
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    core4.util.tool.Singleton._instances = {}
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


@pytest.fixture(autouse=True)
def folder_home():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "../..")
    os.environ["CORE4_OPTION_folder__home"] = os.path.abspath(filename)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)[MONGO_DATABASE]


def test_folder(folder_home):
    intro = CoreIntrospector()
    names = [i["name"] for i in intro.iter_project()]
    assert sorted(names) == ['core4', 'project', 'tests']
