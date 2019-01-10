import logging
import os
import re
import sys

import pymongo
import pytest

import core4.base
import core4.base.collection
import core4.config
import core4.config.tag
import core4.error
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


class MyConfig(core4.config.main.CoreConfig):
    cache = False


class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):
    config_class = MyConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()

    def _make_config(self, *args, **kwargs):
        return MyConfig(*args, **kwargs)


def test_base():
    b = core4.base.CoreBase()
    assert "core4.base.main.CoreBase" == b.qual_name()
    assert "core4.base.main.CoreBase" == b.qual_name(short=False)


def test_project():
    import project.test
    t = project.test.Test()
    assert "project" == t.project
    assert "project.test.Test" == t.qual_name()
    assert "core4.project.project.test.Test", t.qual_name(short=False)
    assert "project.test.Test()" == repr(t)


def test_project_conf():
    import project.test
    t = project.test.Test()
    assert t.project_config().endswith("core4/project/project.yaml")
    assert t.config.mongo_database, "core4test"
    assert repr(t) == "project.test.Test()"
    assert "/core4test/sys.role" in t.config.sys.role.info_url


def test_main():
    import project.test
    from subprocess import check_output
    environ = os.environ
    if "PYTHONPATH" in os.environ:
        pp = os.environ["PYTHONPATH"].split(":")
    else:
        pp = []
    pp.append(os.path.dirname(core4.__file__) + "/..")
    os.environ["PYTHONPATH"] = ":".join(pp)
    out = check_output([sys.executable, project.test.__file__], env=environ)
    assert out.decode(
        "utf-8").strip() == 'core4.base.main.CoreBase project.test.Test'


def test_collection_scheme():
    coll1 = core4.base.collection.CoreCollection(
        scheme="mongodb",
        hostname="localhost:27017",
        database="core4test",
        collection="sys.log",
        username="core",
        password="654321"
    )
    os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
    a = LogOn()
    a.logger.info("hello world")
    import pprint
    pprint.pprint(list(coll1.find()))
    assert coll1.count_documents({}) == 1
    with pytest.raises(core4.error.Core4ConfigurationError):
        core4.base.collection.CoreCollection(
            scheme="mongoxxx",
            hostname="localhost:27017",
            database="core4test",
            collection="sys.log",
            username="core",
            password="654321"
        )


def test_progress(mongodb):
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    bc = LogOn()
    bc.progress(0.01)
    bc.progress(0.04)  # suppress
    bc.progress(0.05)
    bc.progress(0.05)  # suppress
    bc.progress(0.08)
    bc.progress(0.09)  # suppress
    bc.progress(0.12)  # suppress
    data = list(mongodb.core4test.sys.log.find({"message":
                                                    {"$regex": "progress"}}))
    assert 3 == len(data)
    for i, check in enumerate([0, 5, 10]):
        assert re.search("{}%$".format(check), data[i]["message"])


def test_progress_restart(mongodb):
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    bc = LogOn()
    bc.progress(0.01)
    bc.progress(0.05)
    bc.progress(0.10)
    bc.progress(0.15)
    bc.progress(0.09)
    bc.progress(0.08)  # suppress
    bc.progress(0.50)
    bc.progress(0.10)  # restart
    data = list(mongodb.core4test.sys.log.find({"message":
                                                    {"$regex": "progress"}}))
    assert 7 == len(data)
    for i, check in enumerate([0, 5, 10, 15, 10, 50, 10]):
        assert re.search("{}%$".format(check), data[i]["message"])


def test_custom_progress(mongodb):
    bc = LogOn()
    bc.progress(0.01, inc=0.1)
    bc.progress(0.05, inc=0.1)
    bc.progress(0.10, inc=0.1)
    bc.progress(0.15, inc=0.1)
    bc.progress(0.18, inc=0.1)
    bc.progress(0.20, inc=0.1)
    bc.progress(0.22, inc=0.1)
    bc.progress(0.25, inc=0.1)
    bc.progress(0.28, inc=0.1)
    data = list(mongodb.core4test.sys.log.find({"message":
                                                    {"$regex": "progress"}}))
    assert 4 == len(data)
    for i, check in enumerate([0, 10, 20, 30]):
        assert re.search("{}%$".format(check), data[i]["message"])


def test_progress_message(mongodb):
    bc = LogOn()
    bc.progress(0.01, "hello %s: %1.2f", "world", 0.01, inc=0.1)
    bc.progress(0.12, "hello %s: %1.2f", "world", 0.12, inc=0.1)
    data = list(mongodb.core4test.sys.log.find({"message":
                                                    {"$regex": "progress"}}))
    assert 2 == len(data)
    assert data[0]["message"] == "progress at 0% - hello world: 0.01"
    assert data[1]["message"] == "progress at 10% - hello world: 0.12"


def test_unwind_config(mongodb):
    os.environ["CORE4_CONFIG"] = asset("base/local.yaml")
    import core4.config.test

    class XConfig(core4.config.test.TestConfig):
        cache = False

    class A(LogOn):
        def _make_config(self, *args, **kwargs):
            kwargs["local_dict"] = {
                "tests": {
                    "test_base": {
                        "A": {
                            "log_level": "WARNING"
                        }
                    }
                },
                "sys": {
                    "log": core4.config.tag.ConnectTag(
                        "mongodb://core:654321@localhost:27017"
                        "/core4test/sys.log")
                },
                "logging": {
                    "mongodb": "DEBUG"
                }

            }
            return XConfig(*args, **kwargs)

    a = A()
    assert "WARNING" == a.config.tests.test_base.A.log_level
    assert "WARNING" == a.log_level
    b = core4.base.CoreBase()
    print("HE?", b.log_level)
    for o in [a, b]:
        o.logger.debug("this is debug")
        o.logger.info("this is info")
        o.logger.warning("this is warning")
        o.logger.error("this is error")

    coll1 = core4.base.collection.CoreCollection(
        scheme="mongodb",
        hostname="localhost:27017",
        database="core4test",
        collection="sys.log",
        username="core",
        password="654321"
    )
    data = list(coll1.find())
    for l in data:
        print(l)
    assert 0 == sum([1 for i in data if i["level"] == "DEBUG"])
    assert 1 == sum([1 for i in data if i["level"] == "INFO"])
    assert 2 == sum([1 for i in data if i["level"] == "WARNING"])
    assert 2 == sum([1 for i in data if i["level"] == "ERROR"])


def test_message_format():
    b = core4.base.CoreBase()
    assert b.format_args() == ""
    assert b.format_args("hello") == "hello"
    assert b.format_args("hello %s", "world") == "hello world"
    assert b.format_args("hello %(name)s", name="world") == "hello world"
    assert b.format_args("hello %(name)s") == "hello %(name)s"


def test_version():
    base = core4.base.main.CoreBase()
    assert base.version() == core4.__version__
