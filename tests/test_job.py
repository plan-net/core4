# -*- coding: utf-8 -*-

import os
import unittest

import pymongo
import datetime as dt

import core4.base
import core4.config.test
import core4.error
import core4.queue.job
import tests.util
import tests.util
import core4.util
import core4.base.cookie

class TestJob(unittest.TestCase):

    def setUp(self):
        self.tearDown()
        self.mongo.drop_database('core4test')
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321" \
                                                 "@localhost:27017"
        os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        class LogOn(core4.base.main.CoreBase,
                    core4.logger.mixin.CoreLoggerMixin): pass
        logon = LogOn()
        logon.setup_logging()

    def tearDown(self):
        tests.util.drop_env()

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

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
                                "progress_interval": 5, # todo: obsolete?
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
                                    "progress_interval": 10, # todo: dito?
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
        self.assertEqual(job.progress_interval, 10)
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
        self.assertEqual("1 * * * *", job.schedule)
        self.assertEqual(2, job.attempts)

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

    def test_frozen_init(self):
        class MyJob(core4.queue.job.CoreJob):

            author = 'mra'

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={},
                    local_dict={},
                    **kwargs
                )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.author = "abc"

        with self.assertRaises(core4.error.Core4UsageError):
            _ = MyJob()

    def test_frozen_method(self):
        class MyJob(core4.queue.job.CoreJob):

            author = 'mra'

            def make_config(self, *args, **kwargs):
                return core4.config.test.TestConfig(
                    plugin_name="tests",
                    plugin_dict={},
                    local_dict={},
                    **kwargs
                )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

            def test(self):
                self.state = 'RUNNING'

        job = MyJob()
        with self.assertRaises(core4.error.Core4UsageError):
            job.test()

    def test_progress(self):
        # todo: this test produces the following output if DEBUG is on (see .setup, above). Please explain
        """
        Testing started at 09:00 ...
        /home/mra/.virtualenvs/core4dev/bin/python /snap/pycharm-community/85/helpers/pycharm/_jb_unittest_runner.py --target test_job.TestJob.test_progress
        Launching unittests with arguments python -m unittest test_job.TestJob.test_progress in /home/mra/PycharmProjects/core4/tests
        2018-09-27 07:00:36,629 - DEBUG    [tests.test_job.LogOn/None] stderr logging setup complete, level DEBUG
        2018-09-27 07:00:36,629 - DEBUG    [tests.test_job.LogOn/None] logging setup complete
        2018-09-27 07:00:37,662 - DEBUG    [tests.test_job.MyJob/None] slept 0 seconds
        2018-09-27 07:00:42,672 - DEBUG    [tests.test_job.MyJob/None] slept 5 seconds
        2018-09-27 07:00:47,680 - DEBUG    [tests.test_job.MyJob/None] slept 0 seconds
        2018-09-27 07:00:52,691 - DEBUG    [tests.test_job.MyJob/None] slept 5 seconds

        Ran 1 test in 20.145s
        """
        class MyJob(core4.queue.job.CoreJob):
            author = 'mkr'

            def execute(self):
                import time
                for i in range(0, 10, 1):
                    time.sleep(1.0)
                    self.progress(i/10, "slept {} seconds".format(i))

            def defer_self(self):
                import time
                time.sleep(10.0)
                self.defer()

        job = MyJob(_frozen_=False)
        job.__dict__['_id'] = "this is just a test_id"
        locked = {"_id": job._id, "locked": {
        "progress_value": 0.0,
        "host": core4.util.get_hostname(),
        "pid": core4.util.get_pid(),
        "user": core4.util.get_username()
        }}
        job.config.sys.queue.insert_one(locked)
        job.__dict__['locked'] = locked['locked']
        # execute ones by calling execute directly to check job-runtime progress
        job.execute()
        expected = {
                    "_id": "this is just a test_id",
                    "locked": {
                    "progress_value": 0.5,
                    "host": core4.util.get_hostname(),
                    "pid": core4.util.get_pid(),
                    "user": core4.util.get_username(),
                    "progress": "slept 5 seconds"
                        }
                    }
        actual = job.config.sys.queue.find_one({"_id": job._id})
        self.assertEqual(expected['locked']['host'], actual['locked']['host'])
        self.assertEqual(expected['locked']['user'], actual['locked']['user'])
        self.assertEqual(expected['locked']['pid'], actual['locked']['pid'])
        self.assertEqual(expected['locked']['progress_value'], actual['locked']['progress_value'])
        self.assertEqual(expected['locked']['progress'], actual['locked']['progress'])
        job.run()
        actual = job.config.sys.queue.find_one({"_id": job._id})
        self.assertEqual(1.0, actual['locked']['progress_value'])
        self.assertEqual("execution end marker", actual['locked']['progress'])

    def test_defer(self):
        class DeferJob(core4.queue.job.CoreJob):
            author = 'mkr'
            defer_self = True
            progress_interval = 1

            def execute(self):
                import time
                time.sleep(1)
                if self.defer_self:
                    self.defer_self = False
                    self.defer("defer for testing")
                time.sleep(1)

            def progress_with_format_single(self):
                self.progress(0.2, "Testing %s with format", "progress")

            def progress_with_format_multiple(self):
                # we do have to sleep here to allow this progress-message to come through with default-settings
                import time
                time.sleep(1)
                self.progress(0.5, "Testing %s with %d format", "progress", 2)

            def progress_without_comment(self):
                import time
                time.sleep(1)
                self.progress(0.7)


        defer_job = DeferJob()
        defer_job.__dict__['_id'] = "this is test_defer"

        locked = {"_id": defer_job._id,
                  "locked": {
            "progress_value": 0.0,
            "host": core4.util.get_hostname(),
            "pid": core4.util.get_pid(),
            "user": core4.util.get_username()
        }}
        defer_job.__dict__['locked'] = locked['locked']
        defer_job.config.sys.queue.insert_one(locked)

        defer_job.progress_with_format_single()
        actual = defer_job.config.sys.queue.find_one({"_id": defer_job._id})
        self.assertEqual(0.2, actual['locked']['progress_value'])
        self.assertEqual("Testing progress with format", actual['locked']['progress'])
        defer_job.progress_with_format_multiple()
        actual = defer_job.config.sys.queue.find_one({"_id": defer_job._id})
        self.assertEqual(0.5, actual['locked']['progress_value'])
        self.assertEqual("Testing progress with 2 format", actual['locked']['progress'])
        defer_job.progress_without_comment()
        actual = defer_job.config.sys.queue.find_one({"_id": defer_job._id})
        self.assertEqual(0.7, actual['locked']['progress_value'])
        self.assertEqual("", actual['locked']['progress'])

        with self.assertRaises(core4.error.CoreJobDeferred):
            defer_job.run()
        defer_job.run()
        actual = defer_job.config.sys.queue.find_one({"_id": defer_job._id})
        self.assertEqual(actual['locked']['progress_value'], 1.0)
        self.assertEqual(actual['locked']['progress'], "execution end marker")
        self.assertGreaterEqual(actual['locked']['runtime'], 2)
        actual = defer_job.config.sys.cookie.find_one({"_id": defer_job.qual_name()})
        self.assertLess(actual['last_runtime'], dt.datetime.now())


    def test_execute_notImplemented(self):
        class ExecuteNotImplemented(core4.queue.job.CoreJob):
            author = "mkr"

        exec_job = ExecuteNotImplemented()
        with self.assertRaises(NotImplementedError):
            exec_job.run()
        with self.assertRaises(NotImplementedError):
            exec_job.execute()

    def test_cookie(self):
        class JobCookie(core4.queue.job.CoreJob):
            author = "mkr"

        cookie_job = JobCookie()
        self.assertTrue(cookie_job.cookie.cookie_name, "tests.test_job.JobCookie")


if __name__ == '__main__':
    unittest.main()
