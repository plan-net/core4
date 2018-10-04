# import core4.logger.mixin
# import pymongo
# import pytest
# import logging
# import os
# import core4.base.main
# import importlib
#
#
# ASSET_FOLDER = 'asset'
# MONGO_URL = 'mongodb://core:654321@localhost:27017'
# MONGO_DATABASE = 'core4test'
#
# @pytest.fixture(autouse=True)
# def reset(tmpdir):
#     logging.shutdown()
#     # setup
#     conn = pymongo.MongoClient(MONGO_URL)
#     conn.drop_database(MONGO_DATABASE)
#
#     # singletons
#     core4.util.Singleton._instances = {}
#     # os environment
#     dels = []
#     for k in os.environ:
#         if k.startswith('CORE4_'):
#             dels.append(k)
#     for k in dels:
#         del os.environ[k]
#     # logging mixin (setup complete)
#     core4.logger.mixin.CoreLoggerMixin.completed = False
#
#     os.environ[
#         "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321@" \
#                                              "localhost:27017"
#     os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
#     os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
#     yield conn
#     # teardown database
#     conn.drop_database(MONGO_DATABASE)
#     # singletons
#     core4.util.Singleton._instances = {}
#     # os environment
#     dels = []
#     for k in os.environ:
#         if k.startswith('CORE4_'):
#             dels.append(k)
#     for k in dels:
#         del os.environ[k]
#     # logging mixin (setup complete)
#     core4.logger.mixin.CoreLoggerMixin.completed = False
#
# @pytest.fixture
# def mongodb():
#     return pymongo.MongoClient(MONGO_URL)
#
#
# def asset(*filename, exists=True):
#     dirname = os.path.dirname(__file__)
#     filename = os.path.join(dirname, ASSET_FOLDER, *filename)
#     if not exists or os.path.exists(filename):
#         return filename
#     raise FileNotFoundError(filename)
#
#
# def test_log(mongodb):
#     os.environ["CORE4_CONFIG"] = asset("logger/simple.yaml")
#     core4.logger.mixin.logon()
#     b = core4.base.main.CoreBase()
#     b.logger.debug("this is DEBUG")
#     b.logger.info("this is INFO")
#     b.logger.warning("this is WARNING")
#     b.logger.error("this is ERROR")
#     b.logger.critical("this is CRITICAL")
#     data = list(mongodb.core4test.sys.log.find())
#     print(data)
#     assert 1 == sum([1 for i in data if i["level"] == "INFO"])
#     assert 3 == sum([1 for i in data if i["level"] == "DEBUG"])
#     assert 1 == sum([1 for i in data if i["level"] == "WARNING"])
#     assert 1 == sum([1 for i in data if i["level"] == "ERROR"])
#     assert 1 == sum([1 for i in data if i["level"] == "CRITICAL"])



# -*- coding: utf-8 -*-

import glob
import logging
import os
import unittest
import importlib

import pymongo

import core4.base
import core4.config
import core4.error
import core4.logger
import core4.config.test
import project.ident
import tests.util
import core4.util


class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):

    cache = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()


class TestLogging(unittest.TestCase):

    def setUp(self):
        tests.util.drop_env()

        logging.shutdown()
        importlib.reload(logging)
        core4.util.Singleton._instances = {}
        core4.logger.mixin.CoreLoggerMixin.completed = False

        self.mongo.drop_database('core4test')
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321@" \
                                                 "localhost:27017"
        os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/empty.yaml")

    def drop_logs(self):
        for fn in glob.glob("*.log*"):
            #print("removed", fn)
            os.unlink(fn)

    def tearDown(self):
        self.drop_logs()
        tests.util.drop_env()
        logging.shutdown()
        importlib.reload(logging)
        core4.util.Singleton._instances = {}
        self.drop_logs()
        core4.logger.mixin.CoreLoggerMixin.completed = False

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_log(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        b = LogOn()
        b.logger.debug("this is DEBUG")
        b.logger.info("this is INFO")
        b.logger.warning("this is WARNING")
        b.logger.error("this is ERROR")
        b.logger.critical("this is CRITICAL")
        data = list(self.mongo.core4test.sys.log.find())
        self.assertEqual(3, sum([1 for i in data if i["level"] == "DEBUG"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "INFO"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "WARNING"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "ERROR"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "CRITICAL"]))

    def test_exception(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        b = LogOn()
        try:
            x = 1 / 0
        except:
            b.logger.critical("this is so critical", exc_info=True)
        data = list(self.mongo.core4test.sys.log.find(
            {"exception": {"$ne": None}}))
        self.assertEqual(1, len(data))
        out = "\n".join(data[0]["exception"]["text"])
        self.assertIn("division by zero", out)

    def test_exception2(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        b = LogOn()
        try:
            raise RuntimeError("this is a manual runtime error")
        except:
            b.logger.critical("this is so critical", exc_info=True)
        data = list(self.mongo.core4test.sys.log.find(
            {"exception": {"$ne": None}}))
        self.assertEqual(1, len(data))
        self.assertEqual(data[0]["exception"]["info"],
                         "RuntimeError('this is a manual runtime error',)")
        out = "\n".join(data[0]["exception"]["text"])
        self.assertIn("RuntimeError: this is a manual runtime error", out)

    def test_inconsistent_setup(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/error.yaml")
        self.assertRaises(core4.error.Core4SetupError, lambda: LogOn())

    def test_extra_logging(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/extra.yaml")
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        b.logger.info("this is an INFO message")
        b.logger.warning("this is a WARNING message")
        b.logger.error("this is an ERROR message")
        b.logger.critical("this is a CRITICAL error message")
        data = {}
        for fn in glob.glob("*.log*"):
            with open(fn, "r", encoding="utf-8") as f:
                body = f.read()
            k = fn.split(".")[0]
            if not k in data:
                data[k] = []
            data[k] += body.strip().splitlines()
        # for k in data:
        #     print("\n".join(data[k]))
        self.assertEqual(2, len(data["errors"]))
        self.assertEqual(5, len(data["info"]))

    def test_exception_disabled(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        os.environ["CORE4_OPTION_logging__mongodb"] = ""
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        data = list(b.config.sys.log.find())
        self.assertEqual(data, [])

    def test_exception_in_debug(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stdout"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stderr"] = ""
        os.environ["CORE4_OPTION_logging__exception__capacity"] = "!!int 2"
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        b.logger.info("this is an INFO message")
        b.logger.warning("this is a WARNING message")
        b.logger.error("this is an ERROR message")
        b.logger.critical("this is a CRITICAL error message")
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        self.assertEqual({"DEBUG"}, set([d["level"] for d in data[:2]]))
        self.assertEqual(3, sum([1 for d in data if d["level"] == "DEBUG"]))
        self.assertEqual(1, sum([1 for d in data if d["level"] == "WARNING"]))

    def test_identifier(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        b = LogOn()
        b.logger.debug("*** START ***")
        ident = project.ident.Controller()
        ident.execute()
        b.logger.debug("*** END ***")

    def test_massive(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stderr"] = ""
        os.environ["CORE4_OPTION_logging__stdout"] = ""
        LogOn()
        m = project.ident.Massive()
        m.execute()
        data = list(m.config.sys.log.find())
        idented = sum([1 for i in data if i["identifier"] == "0815"])
        self.assertEqual(700, idented)

    def test_format(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.yaml")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        b = LogOn()
        b.logger.info("hello %s", "world")
        data = list(b.config.sys.log.find())
        self.assertEqual("hello world", data[-1]["message"])

    def test_module_logging(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/module.yaml")
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        b.logger.info("this is an INFO message")
        b.logger.warning("this is a WARNING message")
        b.logger.error("this is an ERROR message")
        b.logger.critical("this is a CRITICAL error message")
        import requests
        r = requests.get('http://localhost:27017')
        self.assertEqual(200, r.status_code)
        data = list(b.config.sys.log.find())
        expected = ["extra logging setup",
                    "logging setup",
                    "DEBUG message",
                    "INFO message",
                    "WARNING message",
                    "ERROR message",
                    "CRITICAL error message",
                    "Starting new HTTP connection",
                    "http://localhost:27017"]
        for i, e in enumerate(expected):
            self.assertIn(e, data[i]["message"])

        log = logging.getLogger("root")
        x = list(log.handlers)
        for i in x:
            log.removeHandler(i)
            i.flush()
            i.close()
        expected = ['tests.test_logger.LogOn'] * 7 + [None] * 2
        for i, e in enumerate(expected):
            self.assertEqual(e, data[i]["qual_name"])
        with open("info.log", "r") as fh:
            content = fh.read()
        body = content.splitlines()
        expected = ["mixin"] * 2 + ["test_logger"] * 5 + ["connectionpool"] * 2
        # print("FILE")
        # print(content)
        for i, e in enumerate(expected):
            self.assertIn(e, body[i])

    def test_class_level(self):
        os.environ["CORE4_OPTION_base__log_level"] = "INFO"
        os.environ["CORE4_OPTION_tests__test_logger__C__log_level"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"

        class C(core4.base.CoreBase):
            pass

        class D(core4.base.CoreBase):
            pass

        b = LogOn()
        b.logger.debug("world1")
        b.logger.info("world2")
        c = C()
        self.assertEqual("DEBUG", c.config.tests.test_logger.C.log_level)
        c.logger.debug("world3")
        c.logger.info("hello world4")
        d = D()
        d.logger.debug("world5")
        d.logger.info("hello world6")
        self.assertIsNone(d.config.tests.test_logger.D.log_level)
        data = list(b.config.sys.log.find())
        expected = ['world2', 'world3', 'hello world4', 'hello world6']
        self.assertEqual(expected, [d["message"] for d in data])

    def test_class_level2(self):

        class A(LogOn):

            log_level = "INFO"
            identifier = "A"
            def make_config(self, *args, **kwargs):
                kwargs["local_dict"] = {
                    "tests": {
                        "test_logger": {
                            "A": {
                                "log_level": self.log_level
                            }
                        }
                    },
                    "DEFAULT": {
                        "mongo_url": "mongodb://core:654321@localhost:27017",
                        "mongo_database": "core4test"
                    },
                    "logging": {
                        "mongodb": "DEBUG"
                    }

                }
                return core4.config.test.TestConfig(**kwargs)

            def success(self):
                self.logger.info("start success")
                self.logger.debug("debug message")
                self.logger.info("info message")
                self.logger.info("end success")

        class B(A):
            log_level = "DEBUG"
            identifier = "B"

        a = A()
        b = B()
        a.success()
        b.success()
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        test = [d["level"] for d in data if d["identifier"] == "A"]
        self.assertEqual(test, ["INFO"] * 3)
        test = [d["level"] for d in data if d["identifier"] == "B"]
        self.assertEqual(test, ["INFO", "DEBUG", "INFO", "INFO"])

    def test_exception_usage(self):

        class A(LogOn, core4.logger.mixin.ExceptionLoggerMixin):

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.add_exception_logger()

            def success(self):
                self.logger.info("start")
                self.logger.debug("running")
                self.logger.info("end")

            def failure(self):
                self.logger.critical("this is a failure")

        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = \
            "mongodb://core:654321@localhost:27017"
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        os.environ[
            "CORE4_OPTION_logging__mongodb"] = "INFO"

        a = A()
        a.identifier = 'A'
        a.success()
        a.failure()

        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        expected = ['INFO', 'DEBUG', 'INFO', 'CRITICAL']
        test = [d["level"] for d in data if d["identifier"] == "A"]
        self.assertEqual(test, expected)
        a.success()
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        expected = ['INFO', 'DEBUG', 'INFO', 'CRITICAL', 'INFO', 'INFO']
        test = [d["level"] for d in data if d["identifier"] == "A"]
        self.assertEqual(test, expected)

        b = A()
        b.identifier = 'B'
        b.success()
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        expected = ['INFO', 'INFO']
        test = [d["level"] for d in data if d["identifier"] == "B"]
        self.assertEqual(test, expected)

    def test_log_null(self):

        class A(LogOn):

            log_level = None

            def make_config(self, *args, **kwargs):
                kwargs["local_dict"] = {
                    "tests": {
                        "test_logger": {
                            "A": {
                                "log_level": None
                            }
                        }
                    },
                    "DEFAULT": {
                        "mongo_url": "mongodb://core:654321@localhost:27017",
                        "mongo_database": "core4test"
                    },
                    "logging": {
                        "mongodb": "DEBUG"
                    },
                    "base": {
                        "log_level": None
                    }
                }
                return core4.config.test.TestConfig(**kwargs)

        a = A()
        a.logger.debug("this is DEBUG")
        a.logger.info("this is INFO")
        a.logger.warning("this is WARNING")
        a.logger.error("this is ERROR")
        a.logger.critical("this is CRITICAL")

        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        expected = ['DEBUG', 'DEBUG', 'DEBUG', 'INFO', 'WARNING', 'ERROR',
                    'CRITICAL']
        test = [d["level"] for d in data]
        self.assertEqual(test, expected)


if __name__ == '__main__':
    unittest.main()
