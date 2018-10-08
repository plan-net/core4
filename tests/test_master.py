# -*- coding: utf-8 -*-

import os
import unittest

import pymongo
import time
from threading import Thread

import core4.base.main
import core4.queue.master
import core4.logger.mixin
import tests.util


class TestMaster(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        class LogOn(core4.base.main.CoreBase,
                    core4.logger.mixin.CoreLoggerMixin):
            pass
        logon = LogOn()
        logon.setup_logging()

    def setUp(self):
        self.tearDown()
        self.mongo.drop_database('core4test')
        os.environ["CORE4_OPTION_" \
            "DEFAULT__mongo_url"] = "mongodb://core:654321@localhost:27017"
        os.environ["CORE4_OPTION_" \
            "DEFAULT__mongo_database"] = "core4test"
        os.environ["CORE4_OPTION_" \
            "master__execution_plan__work_jobs"] = "!!int 1"

    def tearDown(self):
        tests.util.drop_env()

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_plan(self):
        master = core4.queue.master.CoreMaster()
        self.assertEqual(len(master.create_plan()), 6)

    def test_5loops(self):
        worker = core4.queue.master.CoreMaster()
        t = Thread(target=worker.start, args=())
        t.start()
        while worker.cycle_no < 5:
            time.sleep(0.5)
        worker.exit = True
        t.join()


if __name__ == '__main__':
    unittest.main()
