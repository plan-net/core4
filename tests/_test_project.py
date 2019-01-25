import logging
import os
import sys
from pprint import pprint

import pymongo
import pytest

import core4.config.main
import core4.service.setup
import core4.util.tool
from core4.queue.scheduler import CoreScheduler
from core4.service.introspect.project import CoreProjectInspector

curr_dir = os.path.abspath(os.curdir)


class MyConfig(core4.config.main.CoreConfig):
    user_config = "_not_found_"
    system_config = "_not_found_"


ORIGINAL_CONFIG_CLASS = core4.config.main.CoreConfig
ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


@pytest.fixture(autouse=True)
def reset(tmpdir):
    core4.config.main.CoreConfig = MyConfig
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    core4.logger.mixin.logon()
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    yield
    conn.drop_database(MONGO_DATABASE)
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
    core4.config.main.CoreConfig = ORIGINAL_CONFIG_CLASS


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)


def test_simple():
    intro = CoreProjectInspector()
    config = intro.check_config_files()
    files = config["files"]
    assert len(files) == 1
    assert os.path.basename(files[0]) == "core4.yaml"
    assert config["database"] is None


def test_normal():
    core4.config.main.CoreConfig = ORIGINAL_CONFIG_CLASS
    intro = CoreProjectInspector()
    _ = intro.check_config_files()
    assert core4.config.main.CoreConfig.__name__ == "CoreConfig"


def test_db_info():
    intro = CoreProjectInspector()
    assert 'core@localhost:27017/core4test/sys.log' == intro.check_mongo_default()


def test_list_project():
    os.environ["CORE4_OPTION_folder__home"] = "/home/mra/core4.prod"
    intro = CoreProjectInspector()
    for folder in intro.list_project():
        pprint(folder)
    #print("\n".join(sys.path))

def test_summary():
    os.environ["CORE4_OPTION_folder__home"] = "/home/mra/core4.prod"
    intro = CoreProjectInspector()
    pprint(intro.summary())


def test_scheduler():
    os.environ["CORE4_OPTION_folder__home"] = "/home/mra/core4.prod"
    s = CoreScheduler()
    s.startup()
    print("OK")