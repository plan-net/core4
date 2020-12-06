# -*- coding: utf-8 -*-

import ctypes
import datetime
import os
import signal
import sys
import threading
import time

import psutil

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import core4.base.main
import core4.logger.mixin
import core4.queue.helper
import core4.queue.helper.job
import core4.queue.helper.job.example
import core4.queue.job
import core4.queue.main
import core4.queue.worker
import core4.util.node

LOOP_INTERVAL = 0.25
libc = ctypes.CDLL(None)

import logging
import os

import pymongo
import pytest

import core4.base
import core4.logger.mixin
import core4.service.setup
import core4.util
import core4.util.tool

ASSET_FOLDER = '../asset'
MONGO_URL = 'mongodb://core:654321@testmongo:27017'
MONGO_DATABASE = 'core4test'


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
    os.environ["CORE4_OPTION_worker__max_cpu"] = "!!int 100"

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
    # ignore signal from children to avoid defunct zombies
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


def setup_thread_excepthook():
    """
    Workaround for `sys.excepthook` thread bug from:
    http://bugs.python.org/issue1230540

    Call once from the main thread before creating any threads.
    """

    init_original = threading.Thread.__init__

    def init(self, *args, **kwargs):

        init_original(self, *args, **kwargs)
        run_original = self.run

        def run_with_except_hook(*args2, **kwargs2):
            try:
                run_original(*args2, **kwargs2)
            except Exception:
                sys.excepthook(*sys.exc_info())

        self.run = run_with_except_hook

    threading.Thread.__init__ = init


setup_thread_excepthook()


@pytest.fixture(autouse=True)
def worker_timing():
    os.environ["CORE4_OPTION_" \
               "worker__execution_plan__work_jobs"] = "!!float {}".format(
        LOOP_INTERVAL)
    os.environ["CORE4_OPTION_" \
               "worker__execution_plan__flag_jobs"] = "!!float 3"


class ProgressJob(core4.queue.job.CoreJob):
    author = "mra"
    progress_interval = 10

    def execute(self, *args, **kwargs):
        runtime = 5.
        tx = core4.util.node.now() + datetime.timedelta(seconds=runtime)
        n = 0
        while True:
            n += 1
            t0 = core4.util.node.now()
            if t0 >= tx:
                break
            p = 1. - (tx - t0).total_seconds() / runtime
            self.progress(p, "at %d", n)
            time.sleep(0.25)


@pytest.mark.timeout(120)
def test_success_after_failure(queue, worker):
    import tests.project.work
    queue.enqueue(tests.project.work.ErrorJob, success=True)
    worker.start(1)
    worker.wait_queue()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if "done execution" in d["message"]]) == 3
    assert sum([1 for d in data if
                "done execution with [failed]" in d["message"]]) == 2
    assert sum([1 for d in data if
                "done execution with [complete]" in d["message"]]) == 1




@pytest.mark.timeout(120)
def test_progress1(queue, worker):
    # fh = open("/tmp/test.txt", "w", encoding="utf-8")
    # fh.write("%s\n" %(os.path.abspath(os.curdir)))
    # fh.write("%s\n" %(sys.executable))
    # fh.close()
    queue.enqueue(ProgressJob)
    worker.start(1)
    worker.wait_queue()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data
                if "progress" in d["message"] and d["level"] == "DEBUG"]) == 2


@pytest.mark.timeout(120)
def test_register(caplog):
    pool = []
    workers = []
    for i in range(1, 4):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i))
        workers.append(worker)
        t = threading.Thread(target=worker.start, args=())
        t.start()
        pool.append(t)
    wait = 3.
    time.sleep(wait)
    for w in workers:
        w.exit = True
    for t in pool:
        t.join()
    for worker in workers:
        assert [i["interval"]
                for i in worker.plan
                if i["name"] == "work_jobs"] == [LOOP_INTERVAL]
        assert [wait / i["interval"]
                for i in worker.plan
                if i["name"] == "work_jobs"][0] >= worker.cycle["total"]


def test_register_duplicate():
    w1 = core4.queue.worker.CoreWorker(name="worker")
    w1.register()
    w2 = core4.queue.worker.CoreWorker(name="worker")
    w2.register()


def test_plan():
    worker = core4.queue.worker.CoreWorker()
    assert len(worker.create_plan()) == 4


@pytest.mark.timeout(120)
def test_5loops():
    worker = core4.queue.worker.CoreWorker()
    t = threading.Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] < 5:
        time.sleep(0.1)
    worker.exit = True
    t.join()


@pytest.mark.timeout(120)
def test_setup():
    worker = core4.queue.worker.CoreWorker()
    worker.exit = True
    worker.start()


# @pytest.mark.timeout(120)
def test_maintenance():
    queue = core4.queue.main.CoreQueue()
    queue.enter_maintenance()
    worker = core4.queue.worker.CoreWorker()
    t = threading.Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] <= 3:
        time.sleep(0.05)
    worker.exit = True
    assert worker.at is None
    t.join()
    del worker.cycle["total"]
    assert worker.cycle == {
        'collect_stats': 0, 'work_jobs': 0, 'flag_jobs': 0, 'remove_jobs': 0}


@pytest.mark.timeout(120)
def test_halt():
    queue = core4.queue.main.CoreQueue()
    queue.halt(now=True)
    time.sleep(1)  # need to wait one second to respect mongo resolution
    worker = core4.queue.worker.CoreWorker()
    t = threading.Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] < 3:
        time.sleep(0.5)
    queue.halt(now=True)
    t.join()


def test_enqueue_dequeue(queue):
    enqueued_job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    worker = core4.queue.worker.CoreWorker()
    doc = worker.get_next_job()
    dequeued_job = queue.job_factory(doc["name"]).deserialise(**doc)
    assert enqueued_job.__dict__.keys() == dequeued_job.__dict__.keys()
    for k in enqueued_job.__dict__.keys():
        if k not in ("logger", "config", "class_config"):
            if enqueued_job.__dict__[k] != dequeued_job.__dict__[k]:
                assert enqueued_job.__dict__[k] == dequeued_job.__dict__[k]


def test_offset():
    queue = core4.queue.main.CoreQueue()
    enqueued_id = []
    for i in range(0, 5):
        enqueued_id.append(queue.enqueue(
            core4.queue.helper.job.example.DummyJob, i=i)._id)
    worker = core4.queue.worker.CoreWorker()
    dequeued_id = []
    dequeued_id.append(worker.get_next_job()["_id"])
    dequeued_id.append(worker.get_next_job()["_id"])
    dequeued_id.append(worker.get_next_job()["_id"])
    enqueued_job = queue.enqueue(core4.queue.helper.job.example.DummyJob, i=5,
                                 priority=10)
    dequeued_job = worker.get_next_job()
    assert enqueued_job._id == dequeued_job["_id"]
    assert enqueued_id[0:len(dequeued_id)] == dequeued_id


def test_lock():
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    queue.enqueue(core4.queue.helper.job.example.DummyJob)
    job = worker.get_next_job()
    assert queue.lock_job(job["_id"], worker.identifier)
    assert queue.lock_job(job["_id"], worker.identifier) is False



def test_remove(mongodb):
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    _id = queue.enqueue(core4.queue.helper.job.example.DummyJob)._id
    assert _id is not None
    assert queue.remove_job(_id)
    job = worker.get_next_job()
    assert job is None
    worker.remove_jobs()
    assert 0 == mongodb.core4test.sys.queue.count_documents({})
    assert 1 == mongodb.core4test.sys.journal.count_documents({})
    worker.cleanup()
    assert 0 == mongodb.core4test.sys.lock.count_documents({})


@pytest.mark.timeout(120)
def test_removing():
    queue = core4.queue.main.CoreQueue()
    pool = []
    workers = []
    count = 10
    for i in range(0, count):
        job = queue.enqueue(core4.queue.helper.job.example.DummyJob, i=i)
        queue.remove_job(job._id)
    for i in range(1, 2):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i))
        workers.append(worker)
        t = threading.Thread(target=worker.start, args=())
        t.start()
        pool.append(t)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.25)
    for w in workers:
        w.exit = True
    for t in pool:
        t.join()
    assert queue.config.sys.queue.count_documents({}) == 0
    assert queue.config.sys.journal.count_documents({}) == count


@pytest.mark.timeout(120)
def test_start_job():
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    worker.cleanup()
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    assert job.identifier == job._id
    assert job._id is not None
    assert job.wall_time is None
    worker.at = core4.util.node.now()
    worker.start_job(job.serialise())
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.5)
    assert queue.config.sys.queue.count_documents({}) == 0
    assert queue.config.sys.journal.count_documents({}) == 1
    job = queue.find_job(job._id)
    assert job.state == "complete"
    print(job.started_at)
    print(job.finished_at)
    print(job.finished_at - job.started_at)
    print(job.runtime)

def test_start_job2(queue):
    threads = 3
    pool = []
    workers = []
    count = 5
    for i in range(0, count):
        queue.enqueue(core4.queue.helper.job.example.DummyJob, i=i)
    for i in range(0, threads):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i + 1))
        workers.append(worker)
        t = threading.Thread(target=worker.start, args=())
        t.start()
        pool.append(t)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    for w in workers:
        w.exit = True
    for t in pool:
        t.join()


@pytest.fixture
def queue():
    return core4.queue.main.CoreQueue()


class WorkerHelper:
    def __init__(self):
        self.queue = core4.queue.main.CoreQueue()
        self.pool = []
        self.worker = []

    def start(self, num=3):
        for i in range(0, num):
            worker = core4.queue.worker.CoreWorker(
                name="worker-{}".format(i + 1))
            self.worker.append(worker)
            t = threading.Thread(target=worker.start, args=())
            self.pool.append(t)
        for t in self.pool:
            t.start()
        print("THREAD ends now")

    def stop(self):
        for worker in self.worker:
            worker.exit = True
        for t in self.pool:
            t.join()

    def wait_queue(self):
        while self.queue.config.sys.queue.count_documents({}) > 0:
            time.sleep(1)
        self.stop()


@pytest.fixture
def worker():
    return WorkerHelper()


@pytest.mark.timeout(120)
def test_ok(queue, worker):
    queue.enqueue(core4.queue.helper.job.example.DummyJob, sleep=0)
    worker.start(1)
    worker.wait_queue()


@pytest.mark.timeout(120)
def test_error(queue, worker):
    import tests.project.work
    queue.enqueue(tests.project.work.ErrorJob)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.25)
        if queue.config.sys.queue.count_documents({"state": "error"}) > 0:
            break
    worker.stop()
    data = list(queue.config.sys.log.find())
    from pprint import pprint
    pprint(data)
    assert sum([1 for d in data if "done execution" in d["message"]]) == 3
    assert sum([1 for d in data if "start execution" in d["message"]]) == 3
    delta = [d["created"] for d in data if
             "execution" in d["message"] and d["level"] == "INFO"]
    assert (delta[1] - delta[0]).total_seconds() >= 3
    assert (delta[2] - delta[1]).total_seconds() >= 3


@pytest.mark.timeout(120)
def test_defer(queue, worker):
    import tests.project.work
    queue.enqueue(tests.project.work.DeferJob)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
        if queue.config.sys.queue.count_documents({"state": "inactive"}) > 0:
            break
    worker.stop()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if
                "done execution with [deferred]" in d["message"]]) > 2
    assert sum([1 for d in data if
                "done execution with [inactive]" in d["message"]]) == 1


@pytest.mark.timeout(120)
def test_mass_defer(queue, worker, mongodb):
    import tests.project.work
    for i in range(0, 10):
        queue.enqueue(tests.project.work.DeferJob, i=i, success=True, defer_time=1,
                      defer_max=2)
    worker.start(4)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
        if queue.config.sys.queue.count_documents({"state": "inactive"}) == 10:
            break
    worker.stop()


@pytest.mark.timeout(120)
def test_fail2inactive(queue, worker, mongodb):
    import tests.project.work
    queue.enqueue(tests.project.work.ErrorJob, defer_max=5, attempts=10)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
        if queue.config.sys.queue.count_documents({"state": "error"}) == 1:
            break
    worker.stop()


@pytest.mark.timeout(120)
def test_remove_failed(queue, worker, mongodb):
    import tests.project.work
    job = queue.enqueue(tests.project.work.ErrorJob, attempts=5, sleep=1)
    worker.start(1)
    while queue.config.sys.queue.count_documents({"state": "running"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0


@pytest.mark.timeout(120)
def test_remove_deferred(queue, worker, mongodb):
    import tests.project.work
    job = queue.enqueue(tests.project.work.DeferJob, defer_time=10)
    worker.start(1)
    while queue.config.sys.queue.count_documents({"state": "deferred"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0


@pytest.mark.timeout(120)
def test_remove_complete(queue, worker, mongodb):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob, sleep=3)
    worker.start(1)
    while queue.config.sys.queue.count_documents({"state": "running"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.state == "complete"


@pytest.mark.timeout(90)
def test_remove_inactive(queue, worker):
    import tests.project.work
    job = queue.enqueue(tests.project.work.DeferJob, defer_max=1)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
        if queue.config.sys.queue.count_documents({"state": "inactive"}) > 0:
            break
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.state == "inactive"


@pytest.mark.timeout(60)
def test_remove_error(queue, worker):
    import tests.project.work
    job = queue.enqueue(tests.project.work.ErrorJob, attempts=1)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
        if queue.config.sys.queue.count_documents({"state": "error"}) > 0:
            break
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.state == "error"


@pytest.mark.timeout(120)
def test_nonstop(queue, worker):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob, sleep=5,
                        wall_time=1)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.1)
        if queue.config.sys.queue.count_documents(
                {"wall_at": {"$ne": None}}) > 0:
            break
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(0.1)
    worker.stop()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.wall_at is not None
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data
                if "successfully set non-stop job" in d["message"]]) == 1


def test_progress2(queue, worker):
    queue.enqueue(ProgressJob, progress_interval=1)
    worker.start(1)
    worker.wait_queue()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data
                if "progress" in d["message"] and d["level"] == "DEBUG"]) >= 5

def test_progress3(queue, worker):

    queue.enqueue(ProgressJob)
    worker.start(1)
    worker.wait_queue()
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data
                if "progress" in d["message"] and d["level"] == "DEBUG"]) == 2


class NoProgressJob(core4.queue.job.CoreJob):
    author = "mra"

    def execute(self, *args, **kwargs):
        time.sleep(3)


@pytest.mark.timeout(120)
def test_zombie(queue, worker):
    job = queue.enqueue(NoProgressJob, zombie_time=1)
    worker.start(1)
    worker.wait_queue()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.zombie_at is not None
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data
                if "successfully set zombie job" in d["message"]]) == 1


class ForeverJob(core4.queue.job.CoreJob):
    author = "mra"

    def execute(self, *args, **kwargs):
        time.sleep(60 * 60 * 24)


@pytest.mark.timeout(120)
def test_no_pid(queue, worker):
    job = queue.enqueue(ForeverJob)
    worker.start(1)
    while True:
        job = queue.find_job(job._id)
        if job.locked and job.locked["pid"]:
            job = queue.find_job(job._id)
            proc = psutil.Process(job.locked["pid"])
            time.sleep(5)
            print("kill now", job.locked["pid"])
            print("my pid", core4.util.node.get_pid())
            proc.kill()
            break
    while True:
        job = queue.find_job(job._id)
        print(job.state)
        if job.state == "killed":
            break
    worker.stop()


@pytest.mark.timeout(120)
def test_kill(queue, worker):
    job = queue.enqueue(ForeverJob, zombie_time=2)
    worker.start(1)
    while True:
        job = queue.find_job(job._id)
        if job.locked and job.locked["pid"]:
            break
    queue.kill_job(job._id)
    while True:
        job = queue.find_job(job._id)
        if job.state == "killed":
            break
    queue.remove_job(job._id)
    worker.wait_queue()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.state == "killed"
    assert job.killed_at is not None


class RestartDeferredTest(core4.queue.job.CoreJob):
    author = 'mra'
    defer_time = 120

    def execute(self, *args, **kwargs):
        if self.trial == 2:
            return
        self.defer("expected deferred")


@pytest.mark.timeout(120)
def test_restart_deferred(queue, worker):
    job = queue.enqueue(RestartDeferredTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "deferred":
            break
    queue.restart_job(job._id)
    worker.wait_queue()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.trial == 2
    assert job.state == core4.queue.job.STATE_COMPLETE


class RestartFailedTest(core4.queue.job.CoreJob):
    author = 'mra'
    error_time = 120
    attempts = 2

    def execute(self, *args, **kwargs):
        if self.trial == 2:
            return
        raise RuntimeError("expected failure")


@pytest.mark.timeout(120)
def test_failed_deferred(queue, worker):
    job = queue.enqueue(RestartFailedTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "failed":
            break
    queue.restart_job(job._id)
    worker.wait_queue()
    assert queue.config.sys.journal.count_documents({}) == 1
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.find_job(job._id)
    assert job.trial == 2
    assert job.state == core4.queue.job.STATE_COMPLETE


class RestartErrorTest(core4.queue.job.CoreJob):
    author = 'mra'
    error_time = 120
    attempts = 1

    def execute(self, *args, **kwargs):
        if self.enqueued["parent_id"] is not None:
            return
        raise RuntimeError("expected failure")


@pytest.mark.timeout(120)
def test_restart_error(queue, worker):
    job = queue.enqueue(RestartErrorTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "error":
            break
    new_id = queue.restart_job(job._id)
    worker.wait_queue()
    assert queue.config.sys.journal.count_documents({}) == 2
    assert queue.config.sys.queue.count_documents({}) == 0
    parent = queue.find_job(job._id)
    assert parent.state == core4.queue.job.STATE_ERROR
    child = queue.find_job(new_id)
    assert child.state == core4.queue.job.STATE_COMPLETE
    assert parent.enqueued["child_id"] == child._id
    assert child.enqueued["parent_id"] == parent._id
    assert parent.enqueued["parent_id"] is None
    assert "child_id" not in child.enqueued
    assert queue.config.sys.lock.count_documents({}) == 0


def test_kill_running_only(queue):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    assert not queue.kill_job(job._id)


class RequiresArgTest(core4.queue.job.CoreJob):
    author = 'mra'

    def execute(self, test, *args, **kwargs):
        pass


@pytest.mark.timeout(120)
def test_requires_arg(queue, worker):
    job = queue.enqueue(RequiresArgTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "error":
            break
    worker.stop()


class RestartKilledTest(core4.queue.job.CoreJob):
    author = 'mra'
    defer_time = 1

    def execute(self, *args, **kwargs):
        if self.enqueued["parent_id"]:
            return
        time.sleep(120)


@pytest.mark.timeout(120)
def test_restart_killed(queue, worker):
    job = queue.enqueue(RestartKilledTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "running":
            break
    queue.kill_job(job._id)
    while True:
        j = queue.find_job(job._id)
        if j.state == "killed":
            break
    new_id = queue.restart_job(job._id)
    queue.restart_job(new_id)
    # queue.remove_job(job._id)
    worker.wait_queue()


class RestartInactiveTest(core4.queue.job.CoreJob):
    author = 'mra'
    defer_max = 5
    defer_time = 1

    def execute(self, *args, **kwargs):
        if self.enqueued["parent_id"]:
            return
        self.defer("expected defer")


@pytest.mark.timeout(120)
def test_restart_inactive(queue, worker):
    job = queue.enqueue(RestartInactiveTest)
    worker.start(1)
    while True:
        j = queue.find_job(job._id)
        if j.state == "inactive":
            break
    queue.restart_job(job._id)
    worker.wait_queue()


class OutputTestJob(core4.queue.job.CoreJob):
    author = 'mra'

    def execute(self, *args, **kwargs):
        print("this output comes from %s" % self.qual_name())
        os.system("echo this comes from echo")
        os.system("echo this comes from stderr > /dev/stderr")
        libc.puts(b"this comes from C")


@pytest.mark.timeout(120)
def test_stdout(queue, worker, mongodb):
    job = queue.enqueue(OutputTestJob)
    worker.start(3)
    worker.wait_queue()
    assert mongodb.core4test.sys.stdout.count_documents({}) == 1
    doc = mongodb.core4test.sys.stdout.find_one()
    print(doc)
    assert doc["_id"] == job._id
    assert ("this output comes from tests.be.test_worker.OutputTestJob"
            in doc["stdout"])
    assert ("this comes from echo" in doc["stdout"])
    assert ("this comes from C" in doc["stdout"])


class BinaryOutputTestJob(core4.queue.job.CoreJob):
    author = 'mra'

    def execute(self, *args, **kwargs):
        sys.stdout.buffer.write(b"evil payload \xDE\xAD\xBE\xEF.")


@pytest.mark.timeout(120)
def test_binary_out(queue, worker, mongodb):
    job = queue.enqueue(BinaryOutputTestJob)
    worker.start(3)
    worker.wait_queue()
    assert mongodb.core4test.sys.stdout.count_documents({}) == 1
    doc = mongodb.core4test.sys.stdout.find_one()
    assert doc["_id"] == job._id
    assert doc["stdout"] == b"evil payload \xDE\xAD\xBE\xEF."


@pytest.mark.timeout(120)
def test_project_maintenance(queue, worker):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    worker.start(1)
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    curr = worker.worker[0].cycle["total"]
    queue.enter_maintenance("core4")
    assert queue.config.sys.queue.count_documents({}) == 0
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    assert queue.config.sys.queue.count_documents({}) == 1
    while worker.worker[0].cycle["total"] < curr + 10:
        time.sleep(1)
    assert queue.config.sys.queue.count_documents({}) == 1
    queue.leave_maintenance("core4")
    worker.wait_queue()
    assert queue.config.sys.queue.count_documents({}) == 0


@pytest.mark.timeout(120)
def test_no_resources(queue):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    worker1 = WorkerNoCPU(name="testRes_1")
    worker2 = WorkerNoCPU(name="testRes_2")
    worker3 = WorkerNoRAM(name="testRes_3")
    worker4 = WorkerNoRAM(name="testRes_4")
    for worker in (worker1, worker2, worker3, worker4):
        worker.at = core4.util.node.now()
        worker.work_jobs()
    assert queue.config.sys.queue.count_documents({"state": "pending"}) == 1
    worker5 = WorkerHasRes(name="testRes")
    worker5.at = core4.util.node.now()
    worker5.work_jobs()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if "skipped job" in d["message"]]) == 4
    assert sum([1 for d in data if "start execution" in d["message"]]) == 1


class WorkerNoCPU(core4.queue.worker.CoreWorker):
    def __init__(self, name):
        super().__init__(name)

    def avg_stats(self):
        return (100, 1024)


class WorkerNoRAM(core4.queue.worker.CoreWorker):
    def __init__(self, name):
        super().__init__(name)

    def avg_stats(self):
        return (0, 30)


@pytest.mark.timeout(120)
def test_no_resources_force(queue):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob, force=True)
    worker = WorkerNoCPU(name="testRes_1")
    worker.at = core4.util.node.now()
    worker.work_jobs()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if "start execution" in d["message"]]) == 1
    job2 = queue.enqueue(core4.queue.helper.job.example.DummyJob, force=True,
                         node="testRes2")
    worker2 = WorkerNoRAM(name="testRes2")
    worker2.at = core4.util.node.now()
    worker2.work_jobs()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if "start execution" in d["message"]]) == 2


@pytest.mark.timeout(120)
def test_worker_has_resources(queue):
    job = queue.enqueue(core4.queue.helper.job.example.DummyJob)
    worker = WorkerNoCPU(name="testRes")
    worker.at = core4.util.node.now()
    worker.start_job(job.serialise())
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    data = list(queue.config.sys.log.find())
    assert sum([1 for d in data if "start execution" in d["message"]]) == 1


class WorkerHasRes(core4.queue.worker.CoreWorker):
    def __init__(self, name):
        super().__init__(name)

    def avg_stats(self):
        return (70, 1024)


@pytest.mark.timeout(120)
def test_project_process(queue):
    queue.enqueue(core4.queue.helper.job.example.DummyJob)
    worker = core4.queue.worker.CoreWorker()
    worker.at = core4.util.node.now()
    worker.work_jobs()
    while queue.config.sys.queue.count_documents({}) > 0:
        print("waiting")
        time.sleep(1)
