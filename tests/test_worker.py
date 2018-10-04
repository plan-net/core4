# -*- coding: utf-8 -*-

import pandas as pd
import time
from threading import Thread

import core4.base.main
import core4.logger.mixin
import core4.queue.job
import core4.queue.main
import core4.queue.worker
import tests.pytest_util
tests.pytest_util.MONGO_LEVEL = "DEBUG"
from tests.pytest_util import *

LOOP_INTERVAL = 0.25


@pytest.fixture(autouse=True)
def worker_timing():
    os.environ["CORE4_OPTION_" \
               "worker__execution_plan__work_jobs"] = "!!float {}".format(
        LOOP_INTERVAL)
    os.environ["CORE4_OPTION_" \
               "worker__execution_plan__nonstop_jobs"] = "!!float 3"


def test_plan():
    worker = core4.queue.worker.CoreWorker()
    assert len(worker.create_plan()) == 6


@pytest.mark.timeout(30)
def test_5loops():
    worker = core4.queue.worker.CoreWorker()
    t = Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] < 5:
        time.sleep(0.1)
    worker.exit = True
    t.join()


@pytest.mark.timeout(30)
def test_setup():
    worker = core4.queue.worker.CoreWorker()
    worker.exit = True
    worker.start()


@pytest.mark.timeout(30)
def test_register(caplog):
    pool = []
    workers = []
    for i in range(1, 4):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i))
        workers.append(worker)
        t = Thread(target=worker.start, args=())
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


@pytest.mark.timeout(30)
def test_maintenance():
    queue = core4.queue.main.CoreQueue()
    queue.enter_maintenance()
    worker = core4.queue.worker.CoreWorker()
    t = Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] < 3:
        time.sleep(0.5)
    worker.exit = True
    assert worker.at is None
    t.join()
    assert worker.cycle == {
        'collect_stats': 0, 'kill_jobs': 0, 'total': 3, 'work_jobs': 0,
        'nonstop_jobs': 0, 'nopid_jobs': 0,
        'remove_jobs': 0}


@pytest.mark.timeout(30)
def test_halt():
    queue = core4.queue.main.CoreQueue()
    queue.halt(now=True)
    worker = core4.queue.worker.CoreWorker()
    t = Thread(target=worker.start, args=())
    t.start()
    while worker.cycle["total"] < 3:
        time.sleep(0.5)
    queue.halt(now=True)
    t.join()


def test_enqueue_dequeue(queue):
    enqueued_job = queue.enqueue(core4.queue.job.DummyJob)
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
        enqueued_id.append(queue.enqueue(core4.queue.job.DummyJob, i=i)._id)
    worker = core4.queue.worker.CoreWorker()
    dequeued_id = []
    dequeued_id.append(worker.get_next_job()["_id"])
    dequeued_id.append(worker.get_next_job()["_id"])
    dequeued_id.append(worker.get_next_job()["_id"])
    enqueued_job = queue.enqueue(core4.queue.job.DummyJob, i=5, priority=10)
    dequeued_job = worker.get_next_job()
    assert enqueued_job._id == dequeued_job["_id"]
    assert enqueued_id[0:len(dequeued_id)] == dequeued_id


def test_lock():
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    queue.enqueue(core4.queue.job.DummyJob)
    job = worker.get_next_job()
    assert queue.lock_job(job["_id"], worker.identifier)
    assert queue.lock_job(job["_id"], worker.identifier) is False


def test_remove(mongodb):
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    _id = queue.enqueue(core4.queue.job.DummyJob)._id
    assert _id is not None
    assert queue.remove_job(_id)
    job = worker.get_next_job()
    assert job is None
    worker.remove_jobs()
    assert 0 == mongodb.core4test.sys.queue.count()
    assert 1 == mongodb.core4test.sys.journal.count()
    worker.cleanup()
    assert 0 == mongodb.core4test.sys.lock.count()


@pytest.mark.timeout(30)
def test_removing():
    queue = core4.queue.main.CoreQueue()
    pool = []
    workers = []
    count = 50
    for i in range(0, count):
        job = queue.enqueue(core4.queue.job.DummyJob, i=i)
        queue.remove_job(job._id)
    for i in range(1, 4):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i))
        workers.append(worker)
        t = Thread(target=worker.start, args=())
        t.start()
        pool.append(t)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
    for w in workers:
        w.exit = True
    for t in pool:
        t.join()
    assert queue.config.sys.queue.count() == 0
    assert queue.config.sys.journal.count() == count


@pytest.mark.timeout(30)
def test_start_job():
    queue = core4.queue.main.CoreQueue()
    worker = core4.queue.worker.CoreWorker()
    worker.cleanup()
    job = queue.enqueue(core4.queue.job.DummyJob)
    assert job.identifier == job._id
    assert job._id is not None
    assert job.wall_time is None
    worker.start_job(job)
    while queue.config.sys.queue.count() > 0:
        time.sleep(0.5)
    assert queue.config.sys.queue.count() == 0
    assert queue.config.sys.journal.count() == 1
    job = queue.find_job(job._id)
    assert job.state == "complete"
    print(job.started_at)
    print(job.finished_at)
    print(job.finished_at - job.started_at)
    print(job.runtime)
    import pandas as pd
    data = list(queue.config.sys.log.find())
    df = pd.DataFrame(data)
    print(df.to_string())


@pytest.mark.timeout(30)
def test_start_job2(queue):
    threads = 3
    pool = []
    workers = []
    count = 5
    for i in range(0, count):
        queue.enqueue(core4.queue.job.DummyJob, i=i)
    for i in range(0, threads):
        worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i + 1))
        workers.append(worker)
        t = Thread(target=worker.start, args=())
        t.start()
        pool.append(t)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
    for w in workers:
        w.exit = True
    for t in pool:
        t.join()

    import pandas as pd
    data = list(queue.config.sys.log.find())
    df = pd.DataFrame(data)
    df.to_pickle('/tmp/df.pickle')
    print(df[df.level.isin(["WARNING", "ERROR", "CRITICAL"])].to_string())


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
            t = Thread(target=worker.start, args=())
            self.pool.append(t)
        for t in self.pool:
            t.start()

    def stop(self):
        for worker in self.worker:
            worker.exit = True
        for t in self.pool:
            t.join()

    def wait_queue(self):
        while self.queue.config.sys.queue.count() > 0:
            time.sleep(1)
        self.stop()


@pytest.fixture
def worker():
    return WorkerHelper()


@pytest.mark.timeout(30)
def test_ok(queue, worker):
    queue.enqueue(core4.queue.job.DummyJob)
    worker.start(1)
    worker.wait_queue()


@pytest.mark.timeout(30)
def test_error(queue, worker):
    import project.work
    queue.enqueue(project.work.ErrorJob)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "error"}) > 0:
            break
    worker.stop()
    df = pd.DataFrame(list(queue.config.sys.log.find()))
    df.to_pickle('/tmp/df.pickle')
    assert df[df.message.str.find("done execution") >= 0].shape[0] == 3
    assert df[df.message.str.find("start execution") >= 0].shape[0] == 3
    x = pd.to_timedelta(
        df[((df.message.str.find("execution") >= 0) & (df.level == "INFO"))
           ].created.diff()).apply(lambda r: r.total_seconds()).tolist()
    assert [x[i] >= 5 for i in [1, 2]] == [True, True]


@pytest.mark.timeout(30)
def test_success_after_failure(queue, worker):
    import project.work
    queue.enqueue(project.work.ErrorJob, success=True)
    worker.start(1)
    worker.wait_queue()
    worker.stop()
    df = pd.DataFrame(list(queue.config.sys.log.find()))
    assert df[df.message.str.find("start execution") >= 0].shape[0] == 3
    assert df[df.message.str.find(
        "done execution with [failed]") >= 0].shape[0] == 2
    assert df[df.message.str.find(
        "done execution with [complete]") >= 0].shape[0] == 1


@pytest.mark.timeout(90)
def test_defer(queue, worker):
    import project.work
    queue.enqueue(project.work.DeferJob)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "inactive"}) > 0:
            break
    worker.stop()
    df = pd.DataFrame(list(queue.config.sys.log.find()))
    assert df[df.message.str.find(
        "done execution with [deferred]") >= 0].shape[0] > 2
    assert df[df.message.str.find(
        "done execution with [inactive]") >= 0].shape[0] == 1

@pytest.mark.timeout(90)
def test_mass_defer(queue, worker, mongodb):
    import project.work
    for i in range(0, 10):
        queue.enqueue(project.work.DeferJob, i=i, success=True, defer_max=5)
    worker.start(4)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "inactive"}) == 10:
            break
    worker.stop()

@pytest.mark.timeout(30)
def test_fail2inactive(queue, worker, mongodb):
    import project.work
    queue.enqueue(project.work.ErrorJob, defer_max=15, attempts=5)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "inactive"}) == 1:
            break
    worker.stop()

@pytest.mark.timeout(30)
def test_remove_failed(queue, worker, mongodb):
    import project.work
    job = queue.enqueue(project.work.ErrorJob, attempts=5, sleep=10)
    worker.start(1)
    while queue.config.sys.queue.count({"state": "running"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count() > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0

@pytest.mark.timeout(30)
def test_remove_deferred(queue, worker, mongodb):
    import project.work
    job = queue.enqueue(project.work.DeferJob, defer_time=10)
    worker.start(1)
    while queue.config.sys.queue.count({"state": "deferred"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count() > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0

@pytest.mark.timeout(30)
def test_remove_complete(queue, worker, mongodb):
    job = queue.enqueue(core4.queue.job.DummyJob, sleep=10)
    worker.start(1)
    while queue.config.sys.queue.count({"state": "running"}) == 0:
        time.sleep(0.25)
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count() > 0:
        time.sleep(0.25)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0
    job = queue.find_job(job._id)
    assert job.state == "complete"

@pytest.mark.timeout(90)
def test_remove_inactive(queue, worker):
    import project.work
    job = queue.enqueue(project.work.DeferJob)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "inactive"}) > 0:
            break
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0
    job = queue.find_job(job._id)
    assert job.state == "inactive"

@pytest.mark.timeout(30)
def test_remove_error(queue, worker):
    import project.work
    job = queue.enqueue(project.work.ErrorJob)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"state": "error"}) > 0:
            break
    assert queue.remove_job(job._id)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0
    job = queue.find_job(job._id)
    assert job.state == "error"


def test_nonstop(queue, worker):
    job = queue.enqueue(core4.queue.job.DummyJob, sleep=10, wall_time=5)
    worker.start(1)
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
        if queue.config.sys.queue.count({"wall_at": {"$ne": None}}) > 0:
            break
    while queue.config.sys.queue.count() > 0:
        time.sleep(1)
    worker.stop()
    assert queue.config.sys.journal.count() == 1
    assert queue.config.sys.queue.count() == 0
    job = queue.find_job(job._id)
    assert job.wall_at is not None




"""
                              _hash                       _id                       args  attempts  attempts_left chain  defer_time dependency                                           enqueued  error_time         finished_at  force         inactive_at killed_at                                         last_error locked max_parallel                   name  priority  progress_interval python query_at removed_at  runtime sources          started_at     state  trial wall_at wall_time worker
0  9d80399e2f6ec2cf1703098702590845  5bb52a8e34ed0902e2f1409d  {'i': 0, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:25  False 2018-10-03 20:46:37      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      3.0    None 2018-10-03 20:46:22  complete      4    None      None   None
1  92eb6bb86e256744b6dbf48c425e66b2  5bb52a8e34ed0902e2f140a0  {'i': 1, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:26  False 2018-10-03 20:46:37      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:23  complete      4    None      None   None
2  a5de59ec05828ce409f40c345709658b  5bb52a8e34ed0902e2f140a2  {'i': 2, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:26  False 2018-10-03 20:46:37      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:23  complete      4    None      None   None
3  8dc1f7e2c0ac682d3ddb690364b87fc6  5bb52a8e34ed0902e2f140a4  {'i': 3, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:26  False 2018-10-03 20:46:38      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      3.0    None 2018-10-03 20:46:23  complete      4    None      None   None
4  449227654901f1d5dca0b0ad23650525  5bb52a8e34ed0902e2f140a6  {'i': 4, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:27  False 2018-10-03 20:46:38      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:24  complete      4    None      None   None
5  4956177ca15c045e729583b5ac689bf0  5bb52a8e34ed0902e2f140a8  {'i': 5, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:27  False 2018-10-03 20:46:38      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:24  complete      4    None      None   None
6  75357743c83f2124d8229142d5b5092b  5bb52a8e34ed0902e2f140aa  {'i': 6, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:28  False 2018-10-03 20:46:38      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      5.0    None 2018-10-03 20:46:25  complete      4    None      None   None
7  1c785ed5c10452fc4b2b3afb2a5e6863  5bb52a8e34ed0902e2f140ac  {'i': 7, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:28  False 2018-10-03 20:46:39      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:25  complete      4    None      None   None
8  32419a751c28d777f58612a1cb9e2d6b  5bb52a8e34ed0902e2f140ae  {'i': 8, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:28  False 2018-10-03 20:46:39      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      4.0    None 2018-10-03 20:46:25  complete      4    None      None   None
9  e4a5f6e799716e82682fba8b9fd37524  5bb52a8e34ed0902e2f140b0  {'i': 9, 'success': True}         1              0    []           5         []  {'parent': None, 'hostname': 'mra.devops', 'us...         600 2018-10-03 20:46:29  False 2018-10-03 20:46:39      None  {'traceback': ['Traceback (most recent call la...   None         None  project.work.DeferJob         0                  5   None     None       None      5.0    None 2018-10-03 20:46:25  complete      4    None      None   None

In [19]: 
[0]
"""



# #@pytest.mark.timeout(30)
# def test_locking():
#     queue = core4.queue.main.CoreQueue()
#     pool = []
#     workers = []
#     for i in range(0, 50):
#         queue.enqueue(core4.queue.job.DummyJob, i=i)
#     for i in range(1, 4):
#         worker = core4.queue.worker.CoreWorker(name="worker-{}".format(i))
#         workers.append(worker)
#         t = Thread(target=worker.start, args=())
#         t.start()
#         pool.append(t)
#     wait = 10.
#     time.sleep(wait)
#     for w in workers:
#         w.exit = True
#     for t in pool:
#         t.join()


# last_error
# job turns inactive
# query_at mit defer
# remove jobs
# remove inactive
# job turns nonstop (wall_time)

# todo: job turns into zombie

# todo: auto kill if PID was gone

# todo: last_runtime in cookie
# todo: dependency and chain
# todo: custom progress_interval, by DEFAULT, by job
# todo: restarting
# todo: job collection, access management
# todo: max_parallel
# todo: killed
# todo: check all exceptions have logging and log exceptions
# todo: memory logger
# todo: plugin maintenance
# todo: remove killed
