# -*- coding: utf-8 -*-

import os
import sys
import unittest

import pymongo

import core4.base
from core4.base.job import CoreJob, DummyJob

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


    def test_base(self):
        j = CoreJob()
        self.assertEqual("core4.base.job.CoreJob", j.qual_name())
        self.assertEqual("core4.base.job.CoreJob", j.qual_name(short=False))

    # def test_OS_environ(self):
    #     os.environ["CORE4_OPTION_job_defer_time"] = "20"
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
        j = CoreJob(defer_time=60)
        tmp = j.serialize()
        self.assertEqual(60, tmp['defer_time'])

    def test_eq(self):
        j = CoreJob(defer_time=60)
        f = CoreJob(defer_time=60)
        g = CoreJob(defer_time=20)

        self.assertEqual(j,f)
        self.assertEqual(j,f.serialize())
        self.assertNotEqual(j, g)
        self.assertNotEqual(j, g.serialize())

    @unittest.skip
    def test_dummy(self):
        for i in range(20):
            dummy = DummyJob(sleep=60)
            dummyt = DummyJob(sleep=60)
            print(dummy == dummyt)
            print(dummy.__dict__.values())
            print(dummyt.__dict__.values())

            #self.assertEqual(dummy,dummyt)







if __name__ == '__main__':
    unittest.main()
