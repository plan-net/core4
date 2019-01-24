# -*- coding: utf-8 -*-


import logging
import os

import pymongo
import pytest

import core4.base
import core4.base.collection
import core4.config
import core4.config.tag
import core4.config.test
import core4.error
import core4.queue.helper
import core4.queue.helper.job
import core4.queue.helper.job.example
import core4.queue.job
import core4.queue.main
import core4.service.setup
import core4.queue.helper.functool

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


def test_init():
    job = core4.queue.job.CoreJob()
    with pytest.raises(AssertionError):
        job.validate()
    job = core4.queue.helper.job.example.DummyJob()
    assert job._id is None
    assert job.args == {}
    assert job.attempts == 1
    assert job.attempts_left is None
    assert job.author == 'mra'
    assert job.chain == []
    assert job.defer_max == 60 * 60
    assert job.defer_time == 5 * 60
    assert job.dependency == []
    assert job.enqueued is None
    assert job.error_time == 10 * 60
    assert job.finished_at is None
    assert job.inactive_at is None
    # assert job.inactive_time == 30 * 60
    assert job.killed_at is None
    assert job.last_error is None
    assert job.locked is None
    assert job.max_parallel is None
    assert job.worker is None
    assert job.priority == 0
    assert job.name == 'core4.queue.helper.job.example.DummyJob'
    assert job.query_at is None
    assert job.removed_at is None
    assert job.runtime is None
    assert job.schedule is None
    assert job.sources is None
    assert job.started_at is None
    assert job.state is None
    assert job.tag is None
    assert job.wall_at is None
    assert job.wall_time is None


def test_custom_init():
    class MyJob(core4.queue.job.CoreJob):
        author = 'mra'
        defer_time = 1
        tag = ['bli', 'bla', 'blub']

    job = MyJob()
    assert job.name == "tests.test_job.MyJob"
    assert job.author == "mra"
    assert job.defer_time == 1
    assert job.tag == ['bli', 'bla', 'blub']


def test_validation():
    class MyJob(core4.queue.job.CoreJob):
        author = 'mra'
        # defer_time = None
        hidden = True

    job = MyJob()
    job.validate()
    assert job.defer_time == 300
    assert job.hidden is True


def test_validation2():
    class MyJob(core4.queue.job.CoreJob):
        author = 'mra'
        defer_time = None

    job = MyJob()
    with pytest.raises(AssertionError):
        job.validate()


def test_enqueue():
    job = core4.queue.helper.job.example.DummyJob(attempts=10)
    assert job.attempts == 10
    assert job.chain == []

    job = core4.queue.helper.job.example.DummyJob(
        defer_max=1, defer_time=2,  # inactive_time=4,
        max_parallel=5, worker=['A'], priority=6, arg1=100, arg2=200)
    assert job.attempts == 1
    assert job.chain == []
    assert job.defer_max == 1
    assert job.defer_time == 2
    assert job.error_time == 10 * 60
    # assert job.inactive_time == 4
    assert job.max_parallel == 5
    assert job.worker == ['A']
    assert job.priority == 6
    assert job.wall_time is None
    assert job.args == {'arg1': 100, 'arg2': 200}


def test_config_cascade():
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
                    "test_job": {
                        "MyJob": {
                            "defer_time": 666,
                            "defer_max": 777,
                            "progress_interval": 5,
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
                                "progress_interval": 10,
                                "my_var": 'local value',
                                "unknown": 'not defined'
                            }
                        }
                    }
                }, **kwargs
            )

    job = MyJob()
    print(job.config)
    assert job.attempts == 2
    assert job.author == "mra"
    assert job.defer_max == 999
    assert job.progress_interval == 10
    assert job.defer_time == 666
    assert job.config.tests.test_job.MyJob.my_var == "local value"
    assert "unknown" not in job.config.tests.test_job.MyJob
    assert job.class_config.my_var == "local value"
    assert "unknown" not in job.class_config
    assert job.config.tests.section1.key == "section1 value"


def test_invalid_extra_config():
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
                    "test_job": {
                        "MyJob": {
                            "defer_time": "abc"
                        }
                    }
                }, **kwargs
            )

    job = MyJob()
    assert job.class_config.defer_time == "abc"
    with pytest.raises(AssertionError):
        job.validate()


def test_project_overwrite():
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
        schedule = "1 * * * *"

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
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
    assert job.schedule == "2 * * * *"


def test_local_overwrite():
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
        schedule = "1 * * * *"

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
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
    assert job.schedule == "3 * * * *"


def test_class_first():
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
        schedule = "1 * * * *"

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
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
    assert "1 * * * *" == job.schedule
    assert 2 == job.attempts


def test_project_default():
    class MyJob(core4.queue.job.CoreJob):

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={
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
    assert job.schedule is None  # DEFAULT not applied to class config
    assert job.attempts == 2


def test_author_inheritance():
    class MyParent(core4.queue.job.CoreJob):
        author = 'mra'

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={},
                local_dict={},
                **kwargs
            )

    class MyChild(MyParent): pass

    parent = MyParent()
    child = MyChild()

    parent.validate()
    with pytest.raises(AssertionError):
        child.validate()


def test_schedule_inheritance():
    class MyParent(core4.queue.job.CoreJob):
        author = 'mra'
        schedule = '1 * * * *'

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={},
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
    assert child.schedule is None


def test_frozen_init():
    class MyJob(core4.queue.job.CoreJob):
        author = 'mra'

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={},
                local_dict={},
                **kwargs
            )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.author = "abc"

    with pytest.raises(core4.error.Core4UsageError):
        _ = MyJob()


def test_frozen_method():
    class MyJob(core4.queue.job.CoreJob):
        author = 'mra'

        def _make_config(self, *args, **kwargs):
            return core4.config.test.TestConfig(
                project_name="tests",
                project_dict={},
                local_dict={},
                **kwargs
            )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def test(self):
            self.state = 'RUNNING'

    job = MyJob()
    with pytest.raises(core4.error.Core4UsageError):
        job.test()


def test_job_found():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.helper.job.example.DummyJob)


def test_job_not_found():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(core4.error.CoreJobNotFound):
        q.enqueue("DummyJob")


class EnvJob(core4.queue.job.CoreJob):
    author = "mra"
    defer_time = 1
    defer_max = 60 * 60 * 24

    def execute(self, *args, **kwargs):
        self.defer("still waiting")

    def _make_config(self, *args, **kwargs):
        return core4.config.test.TestConfig(
            project_name="tests",
            project_dict={
            },
            local_dict={
                "tests": {
                    "DEFAULT": {
                        "python": "test1"
                    },
                    "test_job": {
                        "EnvJob": {
                            "python": "test2"
                        }
                    }
                }
            }, **kwargs
        )


def test_python():
    job1 = EnvJob()
    import core4.queue.main
    q = core4.queue.main.CoreQueue()
    job2 = q.enqueue(EnvJob, i=1)
    job3 = q.enqueue(EnvJob, python="test99env")
    assert job1.python == job2.python == "test2"
    assert job3.python == "test99env"


class JobTemplate(core4.queue.job.CoreJob,
                  core4.queue.helper.job.base.CoreAbstractJobMixin):
    author = "mra"


class RealJob(JobTemplate):
    def execute(self):
        pass


class RealJobWithAuthor(JobTemplate):
    author = "mra"

    def execute(self):
        pass


def test_abstract_job():
    with pytest.raises(TypeError):
        core4.queue.helper.functool.execute(JobTemplate)

    with pytest.raises(AssertionError):
        core4.queue.helper.functool.execute(RealJob)

    core4.queue.helper.functool.execute(RealJobWithAuthor)
