# -*- coding: utf-8 -*-

import os
import unittest
import tests.util
from core4.base import CoreBase
from core4.logger import CoreLoggerMixin
import core4.error
import core4.config


#LOGGING = True

os.environ["CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"
os.environ["CORE4_CONFIG"] = tests.util.asset('logging', 'simple.conf')
#os.environ["CORE4_OPTION_logging__stderr"] = "DEBUG" if LOGGING else ""


class TestLogging(unittest.TestCase):

    def _reset(self):
        if os.path.exists("test.log"):
            os.unlink("test.log")
        core4.config.CoreConfig.purge_cache()
        mongo = tests.util.mongo_connect()
        mongo["sys.log"].delete_many({})

    def setUp(self):
        if "CORE4_OPTION_logging__config" in os.environ:
            del os.environ["CORE4_OPTION_logging__config"]
        self._reset()

    def tearDown(self):
        self._reset()

    def test_simple(self):

        class A(CoreBase, CoreLoggerMixin):
            pass

        a = A()
        os.environ["CORE4_OPTION_logging__config"] = tests.util.asset(
            'logging', 'logging1.yaml')
        a.setup_logging()
        a.logger.info("info level log message")
        a.logger.debug("debug level log message")
        a.logger.warning("warning level log message")
        a.logger.error("error level log message")
        a.logger.critical("critical level log message")
        with open("test.log", "r") as f:
            body = f.read()
        self.assertEqual(7, len([s for s in body.split("\n") if s]))

    def test_logging_not_found(self):

        fn = tests.util.asset('logging', 'logging1.not_found', exists=False)
        os.environ["CORE4_OPTION_logging__config"] = fn

        class A(CoreBase, CoreLoggerMixin):
            pass

        a = A()
        self.assertRaises(core4.error.Core4SetupError, a.setup_logging)

    def test_mongo(self):

        class A(CoreBase, CoreLoggerMixin):
            pass

        a = A()
        a.setup_logging()
        a.logger.info("hello world")
        a.logger.warning("warning")
        a.logger.debug("hidden debug message")

        mongo = tests.util.mongo_connect()
        self.assertEqual(2, mongo.sys.log.count())


if __name__ == '__main__':
    unittest.main()
