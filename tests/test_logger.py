# -*- coding: utf-8 -*-

import os
import unittest
import pymongo
import core4.base
import core4.logger
import core4.config
import tests.util
from pprint import pprint
import core4.error
import logging
import glob
import plugin.ident


class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()


class TestBase(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        self.mongo.drop_database('core4test')
        os.environ[
            "CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"
        os.environ["CORE4_OPTION_mongo_database"] = "core4test"
        core4.config.CoreConfig._cache = {}

        logger = logging.getLogger(core4.logger.CORE4_PREFIX)
        logger.handlers = []
        core4.logger.CoreLoggerMixin.completed = False
        self.tearDown()

    def tearDown(self):
        for fn in glob.glob("*.log*"):
            #print("removed", fn)
            os.unlink(fn)

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_log(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        b = LogOn()
        b.logger.debug("this is DEBUG")
        b.logger.info("this is INFO")
        b.logger.warning("this is WARNING")
        b.logger.error("this is ERROR")
        b.logger.critical("this is CRITICAL")
        data = list(self.mongo.core4test.sys.log.find())
        # import pandas as pd
        # print(pd.DataFrame(data).to_string())
        self.assertEqual(3, sum([1 for i in data if i["level"] == "DEBUG"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "INFO"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "WARNING"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "ERROR"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "CRITICAL"]))

    def test_exception(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        b = LogOn()
        try:
            x = 1/ 0
        except:
            b.logger.critical("this is so critical", exc_info=True)
        data = list(self.mongo.core4test.sys.log.find(
            {"exception": {"$ne": None}}))
        self.assertEqual(1, len(data))
        out = "\n".join(data[0]["exception"]["text"])
        self.assertIn("division by zero", out)

    def test_exception2(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
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
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/error.py")
        self.assertRaises(core4.error.Core4SetupError, lambda: LogOn())

    def test_cache(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        b = LogOn()
        c = LogOn()

    def test_extra_logging(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/extra.py")
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
            data[k] += body.strip().split("\n")
        self.assertEqual(2, len(data["errors"]))
        self.assertEqual(5, len(data["info"]))

    def test_exception_logging(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        # os.environ["CORE4_OPTION_logging__exception__capacity"] = "2"
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        b.logger.info("this is an INFO message")
        b.logger.warning("this is a WARNING message")
        b.logger.error("this is an ERROR message")
        b.logger.critical("this is a CRITICAL error message")
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        # import pandas as pd
        # print(pd.DataFrame(data).to_string())
        self.assertEqual({"DEBUG"}, set([d["level"] for d in data[:4]]))
        self.assertEqual(4, sum([1 for d in data if d["level"] == "DEBUG"]))

    def test_exception_fifo(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        os.environ["CORE4_OPTION_logging__exception__capacity"] = "2"
        b = LogOn()
        b.logger.debug("this is a DEBUG message")
        b.logger.info("this is an INFO message")
        b.logger.warning("this is a WARNING message")
        b.logger.error("this is an ERROR message")
        b.logger.critical("this is a CRITICAL error message")
        data = list(self.mongo.core4test.sys.log.find(sort=[("_id", 1)]))
        # import pandas as pd
        # print(pd.DataFrame(data).to_string())
        self.assertEqual({"DEBUG"}, set([d["level"] for d in data[:2]]))
        self.assertEqual(2, sum([1 for d in data if d["level"] == "DEBUG"]))
        self.assertEqual(1, sum([1 for d in data if d["level"] == "WARNING"]))

    def test_exception_dsiabled(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = ""
        b = LogOn()
        b.logger.debug("this is a DEBUG message")

    def test_exception_in_debug(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stdout"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stderr"] = ""
        os.environ["CORE4_OPTION_logging__exception__capacity"] = "2"
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
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        b = LogOn()
        b.logger.debug("*** START ***")
        ident = plugin.ident.Controller()
        ident.execute()
        b.logger.debug("*** END ***")

    def test_massive(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("logger/simple.py")
        os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
        os.environ["CORE4_OPTION_logging__stderr"] = ""
        os.environ["CORE4_OPTION_logging__stdout"] = ""
        LogOn()
        m = plugin.ident.Massive()
        m.execute()
        data = list(m.config.kernel["sys.log"].find())
        idented = sum([1 for i in data if i["identifier"] == "0815"])
        self.assertEqual(700, idented)

if __name__ == '__main__':
    unittest.main()
