# -*- coding: utf-8 -*-

import os
import sys
import unittest

import pymongo

import core4.base
from core4.base.job import CoreJob

# import core4.logger
os.environ["CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"


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

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    # def test_something(self):
    #     import time
    #     time.sleep(1)
    #     self.assertEqual(True, True)

    def test_base(self):
        j = CoreJob()
        self.assertEqual("core4.base.job.CoreJob", j.qual_name())
        self.assertEqual("core4.base.job.CoreJob", j.qual_name(short=False))
    #
    # def test_OS_environ(self):
    #     os.environ["CORE4_OPTION_job_max_defertime"] = "20"
    #     j = CoreJob()
    #     self.assertEqual(20, j.defer_time)


   # thy do options not show up in __init__ as kwargs?
    def test_enqueue_options(self):
        f = CoreJob(defer_max=20, defer_time=10)
        self.assertEqual(20, f.defer_max)

    def test_deserialize_default(self):
        j = CoreJob()
        j.deserialize({"defer_max": 10, "defer_time": 10})
        self.assertEqual(10, j.defer_max)
        self.assertEqual(10, j.defer_time)

    def test_serialize(self):
        j = CoreJob()
        tmp = j.serialize()
        self.assertEqual(60, tmp['defer_time'])




if __name__ == '__main__':
    unittest.main()
