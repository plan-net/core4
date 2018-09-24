# -*- coding: utf-8 -*-

import os
import unittest

import pymongo

import core4.base
import core4.config.test
import core4.error
import core4.queue.job
import tests.util
import tests.util


class TestJob(unittest.TestCase):

    def setUp(self):
        self.tearDown()
        self.mongo.drop_database('core4test')
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321" \
                                                 "@localhost:27017"
        os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"

    def tearDown(self):
        tests.util.drop_env()

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    #  def test_deserialize_default(self):
    #      j = CoreJob()
    #      j.deserialize({"defer_max": 10, "defer_time": 10, "_id": 7777})
    #      self.assertEqual(10, j.defer_max)
    #      self.assertEqual(10, j.defer_time)
    #      self.assertEqual(7777, j._id)
    #      a = j.serialize()
    #      g = CoreJob()
    #      g.deserialize(a)
    #      self.assertEqual(10, g.defer_max)
    #      self.assertEqual(10, g.defer_time)
    #
    #  def test_serialize(self):
    #      j = CoreJob(defer_time=60)
    #      tmp = j.serialize()
    #      self.assertEqual(60, tmp['defer_time'])
    #

    def test_init(self):
        job = core4.queue.job.CoreJob()
        with self.assertRaises(AssertionError):
            job.validate()
        job = core4.queue.job.DummyJob()
        self.assertIsNone(job._id)
        self.assertEqual(job.args, {})
        self.assertEqual(job.attempts, 1)
        self.assertIsNone(job.attempts_left)
        self.assertEqual(job.author, 'mra')
        self.assertEqual(job.chain, [])
        self.assertEqual(job.defer_max, 60 * 60)
        self.assertEqual(job.defer_time, 5 * 60)
        self.assertEqual(job.dependency, [])
        self.assertIsNone(job.enqueued)
        self.assertEqual(job.error_time, 10 * 60)
        self.assertIsNone(job.finished_at)
        self.assertIsNone(job.inactive_at)
        self.assertEqual(job.inactive_time, 30 * 60)
        self.assertIsNone(job.killed_at)
        self.assertIsNone(job.last_error)
        self.assertIsNone(job.locked)
        self.assertIsNone(job.max_parallel)
        self.assertIsNone(job.nodes)
        self.assertIsNone(job.nonstop_at)
        self.assertEqual(job.priority, 0)
        self.assertEqual(job.name, 'core4.queue.job.DummyJob')
        self.assertIsNone(job.query_at)
        self.assertIsNone(job.remove_at)
        self.assertIsNone(job.runtime)
        self.assertIsNone(job.schedule)
        self.assertIsNone(job.sources)
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.state)
        self.assertEqual(job.tag, [])
        self.assertIsNone(job.wall_at)
        self.assertIsNone(job.wall_time)
        self.assertIsNone(job.zombie_at)

    def test_custom_init(self):
        class MyJob(core4.queue.job.CoreJob):
            author = 'mra'
            defer_time = 1
            tag = ['bli', 'bla', 'blub']

        job = MyJob()
        self.assertEqual(job.name, "tests.test_job.MyJob")
        self.assertEqual(job.author, "mra")
        self.assertEqual(job.defer_time, 1)
        self.assertEqual(job.tag, ['bli', 'bla', 'blub'])

    def test_validation(self):
        class MyJob(core4.queue.job.CoreJob):
            author = 'mra'
            defer_time = None
            hidden = True

        job = MyJob()
        job.validate()
        self.assertEqual(job.defer_time, 300)
        self.assertTrue(job.hidden)

    def test_enqueue(self):
        job = core4.queue.job.DummyJob(
            attempts=10)
        self.assertEqual(job.attempts, 10)
        self.assertEqual(job.chain, [])

        job = core4.queue.job.DummyJob(
            defer_max=1, defer_time=2, inactive_time=4,
            max_parallel=5, nodes=['A'], priority=6, arg1=100, arg2=200)
        self.assertEqual(job.attempts, 1)
        self.assertEqual(job.chain, [])
        self.assertEqual(job.defer_max, 1)
        self.assertEqual(job.defer_time, 2)
        self.assertEqual(job.error_time, 10 * 60)
        self.assertEqual(job.inactive_time, 4)
        self.assertEqual(job.max_parallel, 5)
        self.assertEqual(job.nodes, ['A'])
        self.assertEqual(job.priority, 6)
        self.assertEqual(job.wall_time, None)
        self.assertEqual(job.args, {'arg1': 100, 'arg2': 200})

    def test_config_cascade(self):
        class MyJob(core4.queue.job.CoreJob):
            author = "mra"

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "test_job": {
                            "MyJob": {
                                "defer_time": 666,
                                "defer_max": 777,
                                "my_var": 'custom value'
                            }
                        },
                        "section1": {
                            "key": "section1 value"
                        }
                    },
                    local_dict={
                        "tests": {
                            "test_job": {
                                "MyJob": {
                                    "attempts": 2,
                                    "author": "fake",
                                    "defer_max": 999,
                                    "my_var": 'local value',
                                    "unknown": 'not defined'
                                }
                            }
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertEqual(job.attempts, 2)
        self.assertEqual(job.author, "mra")
        self.assertEqual(job.defer_max, 999)
        self.assertEqual(job.defer_time, 666)
        self.assertEqual(job.config.tests.test_job.MyJob.my_var, "local value")
        self.assertFalse("unknown" in job.config.tests.test_job.MyJob)
        self.assertEqual(job.class_config.my_var, "local value")
        self.assertFalse("unknown" in job.class_config)
        self.assertEqual(job.config.tests.section1.key, "section1 value")

    def test_invalid_extra_config(self):
        class MyJob(core4.queue.job.CoreJob):
            author = "mra"

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "test_job": {
                            "MyJob": {
                                "defer_time": "abc"
                            }
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertEqual(job.class_config.defer_time, "abc")
        with self.assertRaises(AssertionError):
            job.validate()

    def test_plugin_overwrite(self):
        class MyJob(core4.queue.job.CoreJob):
            author = "mra"
            schedule = "1 * * * *"

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "test_job": {
                            "MyJob": {
                                "schedule": "2 * * * *"
                            }
                        },
                    },
                    local_dict={
                        "tests": {
                            "value": 1
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertEqual(job.schedule, "2 * * * *")

    def test_local_overwrite(self):
        class MyJob(core4.queue.job.CoreJob):
            author = "mra"
            schedule = "1 * * * *"

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "test_job": {
                            "MyJob": {
                                "schedule": "2 * * * *"
                            }
                        },
                    },
                    local_dict={
                        "tests": {
                            "value": 1,
                            "test_job": {
                                "MyJob": {
                                    "schedule": "3 * * * *"
                                }
                            },
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertEqual(job.schedule, "3 * * * *")

    def test_class_first(self):
        class MyJob(core4.queue.job.CoreJob):
            author = "mra"
            schedule = "1 * * * *"

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "test_job": {
                            "MyJob": {
                                "attempts": 1
                            }
                        },
                    },
                    local_dict={
                        "tests": {
                            "value": 1,
                            "test_job": {
                                "MyJob": {
                                    "attempts": 2
                                }
                            },
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertEqual(job.schedule, "1 * * * *")
        self.assertEqual(job.attempts, 2)

    def test_plugin_default(self):
        class MyJob(core4.queue.job.CoreJob):

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={
                        "DEFAULT": {
                            "schedule": "1 * * * *"
                        },
                    },
                    local_dict={
                        "tests": {
                            "value": 1,
                            "test_job": {
                                "MyJob": {
                                    "attempts": 2
                                }
                            },
                        }
                    }, **kwargs
                )

        job = MyJob()
        self.assertIsNone(job.schedule)  # DEFAULT not applied to class config
        self.assertEqual(job.attempts, 2)

    def test_author_inheritance(self):
        class MyParent(core4.queue.job.CoreJob):

            author = 'mra'

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={},
                    local_dict={},
                    **kwargs
                )

        class MyChild(MyParent): pass

        parent = MyParent()
        child = MyChild()

        parent.validate()
        with self.assertRaises(AssertionError):
            child.validate()

    def test_schedule_inheritance(self):
        class MyParent(core4.queue.job.CoreJob):

            author = 'mra'
            schedule = '1 * * * *'

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={},
                    local_dict={
                        "tests": {
                            "test_job": {
                                "MyParent": {
                                    "schedule": "2 * * * *"
                                },
                            }
                        }
                    },
                    **kwargs
                )

        class MyChild(MyParent):
            author = "mra"

        parent = MyParent()
        child = MyChild()

        parent.validate()
        child.validate()
        self.assertIsNone(child.schedule)

    def test_serialise(self):
        job = core4.queue.job.DummyJob()
        job.save()


if __name__ == '__main__':
    unittest.main()
