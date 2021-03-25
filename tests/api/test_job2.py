import json
import time
from pprint import pprint

import tornado.gen as gen
from tornado.ioloop import IOLoop

import core4.queue.helper.job.example
import core4.queue.main
from core4.queue.job import CoreJob
from tests.api.test_job import worker
from tests.api.test_test import setup, mongodb, core4api

_ = setup
_ = mongodb
_ = core4api
_ = worker


class MyJob(CoreJob):
    author = "mra"

    def execute(self):
        for i in range(300):
            self.logger.info("hello world: %d", i)
            # self.progress((i+1) / 3)
            # time.sleep(1)


class MyJob1(CoreJob):
    author = "mra"

    def execute(self):
        time.sleep(5)
        for i in range(300):
            self.logger.info("hello world: %d", i)


class MyJob2(CoreJob):
    author = "mra"

    def execute(self):
        self.logger.info("this is trial [%d]", self.trial)
        for i in range(300):
            self.logger.info("hello world: %d", i)
        if self.trial == 1:
            time.sleep(20)
        for i in range(300, 600):
            self.logger.info("hello world: %d", i)

class MyJob3(CoreJob):
    author = "mra"

    def execute(self):
        for r in range(3):
            for i in range(200):
                self.logger.info("hello world: %d:%d", r, i)
            time.sleep(5)


def parse_sse(body):
    out = body.decode("utf-8")
    states = []
    logs = []
    for pkg in out.split("\n\n"):
        event, *data = pkg.split("\n")
        p = "\n".join(data)[5:]
        if p:
            js = json.loads(p)
            if event == "event: state":
                states.append(js)
            if event == "event: log":
                logs.append(js)
    return states, logs

async def test_simple_post(core4api, worker):
    worker.start(1)
    await core4api.login()
    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "core4.queue.helper.job.example.DummyJob",
              "args": {"sleep": 5}},
        request_timeout=60.)
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    pprint([i["message"] for i in logs])
    pprint(states)
    pprint([i["state"] for i in states])
    assert "complete" in set(sorted(set([i["state"] for i in states])))


class MyJob4(CoreJob):
    author = "mra"

    def execute(self):
        time.sleep(5)
        for i in range(300):
            self.logger.info("hello world: %d", i)
            self.progress(i / 300., force=True)
        time.sleep(10)

async def test_post(core4api, worker):
    worker.start(1)
    await core4api.login()
    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "core4.queue.helper.job.example.DummyJob"},
        request_timeout=60.)
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    assert 'complete' in set(sorted(set([i["state"] for i in states])))
    assert 'running' in set(sorted(set([i["state"] for i in states])))

    assert 1 == sum(
        [1 for i in logs if i["message"].startswith("start execution")])

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob"},
        request_timeout=60.)
    assert resp.code == 200

    states, logs = parse_sse(resp.body)
    assert 'complete' in set(sorted(set([i["state"] for i in states])))
    assert 'running' in set(sorted(set([i["state"] for i in states])))
    assert 300 == sum(
        [1 for i in logs if i["message"].startswith("hello world")])
    worker.stop()


# async def test_lot_progress(core4api, worker):
#     worker.start(1)
#     await core4api.login()
#     resp = await core4api.post(
#         '/core4/api/v1/job',
#         json={"qual_name": "tests.api.test_job2.MyJob4"},
#         request_timeout=60.)
#     assert resp.code == 200
#     states, logs = parse_sse(resp.body)
#     l1 = len(logs)
#     # print(">>>")
#     # pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
#     # print(">>>")
#     # pprint([i["state"] for i in states])
#     assert "complete" in set(sorted(set([i["state"] for i in states])))
#     jid = states[0]["_id"]
#
#     resp = await core4api.get('/core4/api/v1/job/follow/' + jid,
#                                request_timeout=60.)
#     states, logs = parse_sse(resp.body)
#     print(">>>")
#     # pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
#     # print(">>>")
#     # pprint([i["state"] for i in states])
#
#     assert {"complete"} == set(sorted(set([i["state"] for i in states])))
#     assert l1 == len(logs)
#     worker.stop()

# async def test_p3():
#     import sys, os
#     import core4.script.coco as coco
#     from subprocess import check_output
#     os.system(sys.executable + " " + coco.__file__ + " --worker &")
#     time.sleep(10)
#     print("*"*80)
#     out = check_output([sys.executable, coco.__file__, "-x"])
#     print(out)
#     print("OK")

# async def test_log_flow(core4api, worker):
#     #worker.start(1)
#     import sys, os
#     import core4.script.coco as coco
#     from subprocess import check_output
#     os.system(sys.executable + " " + coco.__file__ + " --worker &")
#
#     await core4api.login()
#     resp = await core4api.post(
#         '/core4/api/v1/job',
#         json={"qual_name": "tests.api.test_job2.MyJob3", "follow": False},
#         request_timeout=60.)
#     assert resp.code == 200
#     jid = resp.json()["data"]
#
#     time.sleep(10)
#
#     resp = await core4api.get(
#         '/core4/api/v1/job/follow/' + jid, request_timeout=60.)
#     assert resp.code == 200
#
#     states, logs = parse_sse(resp.body)
#     print(">>>")
#     pprint(["{}: {}".format(i["mode"], i["message"]) for i in logs])
#     #worker.stop()
#     from subprocess import check_output
#     print("*"*80)
#     out = check_output([sys.executable, coco.__file__, "-x"])
#     print(out)
#     print("OK")
#
#     resp = await core4api.get(
#         '/core4/api/v1/job/follow/' + jid, request_timeout=60.)
#     assert resp.code == 200
#
#     states, logs = parse_sse(resp.body)
#     print(">>> 2")
#     pprint(["{}: {}".format(i["mode"], i["message"]) for i in logs])
#
#
class ErrorJob(core4.queue.job.CoreJob):
    """
    This is a simple example job
    """

    author = 'mra'
    error_time = 3
    attempts = 3

    def execute(self, *args, **kwargs):
        if kwargs.get("success", False):
            if self.attempts_left == 1:
                return
        # time.sleep(kwargs.get("sleep", 0))
        raise RuntimeError("expected failure")


async def test_follow(core4api, worker, mongodb):
    worker.start(1)
    await core4api.login()
    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob", "follow": False})
    assert resp.code == 200
    job_id = resp.json()["data"]
    print(job_id)

    resp = await core4api.get('/core4/api/v1/job/follow/' + job_id,
                              request_timeout=60.)
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    assert 300 == sum(
        [1 for i in logs if i["message"].startswith("hello world")])
    worker.stop()


async def test_enqueue_kill_remove(core4api, worker, mongodb):
    worker.start(1)
    await core4api.login()

    async def _kill(_id):
        await gen.sleep(6)
        resp = await core4api.put(
            '/core4/api/v1/job/kill/' + _id,
            request_timeout=220.
        )
        assert resp.code == 200
        print("*" * 80)
        print(resp.body.decode("utf-8"))

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "core4.queue.helper.job.example.DummyJob",
              "args": {"sleep": 30}, "follow": False},
        request_timeout=120.
    )
    assert resp.code == 200

    job_id = resp.json()["data"]

    loop = IOLoop.current()
    loop.spawn_callback(_kill, job_id)

    resp = await core4api.get(
        '/core4/api/v1/job/follow/' + job_id,
        request_timeout=120.
    )
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    assert 'killed' in [i["state"] for i in states]

    resp = await core4api.put(
        '/core4/api/v1/job/remove/' + job_id,
        request_timeout=120.
    )
    assert resp.code == 200

    worker.wait_queue()

    resp = await core4api.put(
        '/core4/api/v1/job/remove/' + job_id,
        request_timeout=120.
    )
    assert resp.code == 404
    worker.wait_queue()
    worker.stop()


async def test_enqueue_kill_restart(core4api, worker, mongodb):
    worker.start(1)
    await core4api.login()

    async def _kill(_id):
        await gen.sleep(10)
        resp = await core4api.put(
            '/core4/api/v1/job/kill/' + _id,
            request_timeout=220.
        )
        assert resp.code == 200

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob2", "follow": False},
        request_timeout=120.
    )
    assert resp.code == 200

    job_id = resp.json()["data"]

    loop = IOLoop.current()
    loop.spawn_callback(_kill, job_id)

    resp = await core4api.get(
        '/core4/api/v1/job/follow/' + job_id,
        request_timeout=220.
    )
    assert resp.code == 200

    resp = await core4api.put(
        '/core4/api/v1/job/restart/' + job_id,
        request_timeout=120.
    )
    assert resp.code == 200

    states, logs = parse_sse(resp.body)
    assert 600 == sum(
        [1 for i in logs if i["message"].startswith("hello world")])

    worker.wait_queue()
    worker.stop()


async def test_error_job(core4api, worker, mongodb):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.ErrorJob", "follow": True},
        request_timeout=120.
    )
    assert resp.code == 200
    worker.stop()
    states, logs = parse_sse(resp.body)
    assert 3 == sum(
        [1 for i in logs if i["message"].startswith("start execution")])


async def test_get(core4api, worker, mongodb):
    await core4api.login()
    q = core4.queue.main.CoreQueue()
    jobs = []
    for i in range(25):
        job = q.enqueue("tests.api.test_job2.MyJob", _i=i, segment=i % 3)
        jobs.append(job._id)

    resp = await core4api.get('/core4/api/v1/job')
    assert resp.code == 200
    assert resp.json()["total_count"] == 25
    assert resp.json()["page_count"] == 3

    resp = await core4api.post('/core4/api/v1/job/queue')
    assert resp.code == 200
    assert resp.json()["total_count"] == 25
    assert resp.json()["page_count"] == 3

    resp = await core4api.post('/core4/api/v1/job/queue',
                               json={"filter": {"args.segment": 0}})
    assert resp.code == 200
    assert resp.json()["total_count"] == 9
    assert resp.json()["page_count"] == 1

    resp = await core4api.get('/core4/api/v1/job/' + str(jobs[0]))
    assert resp.code == 200
    print(resp.json()["data"])

    resp = await core4api.get('/core4/api/v1/job/detail/' + str(jobs[0]))
    assert resp.code == 200
    print(resp.json()["data"])

    resp = await core4api.get(
        '/core4/api/v1/job/detail/5f5c8d3f4bd7a7185cc50353')
    assert resp.code == 404
    print(resp.json()["error"])


async def test_job_log(core4api, worker, mongodb):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob1", "follow": False},
        request_timeout=120.
    )
    assert resp.code == 200
    jid = resp.json()["data"]

    resp = await core4api.get(
        '/core4/api/v1/job/log/' + jid + "?follow=true",
        request_timeout=120.
    )
    assert resp.code == 200
    body = resp.body.decode("utf-8")
    worker.wait_queue()
    worker.stop()
    page = 0
    while True:
        resp = await core4api.get(
            '/core4/api/v1/job/log/' + jid + "?page=" + str(page),
            request_timeout=220.)
        assert resp.code == 200
        print("*" * 10, page, resp.json()["page_count"],
              resp.json()["total_count"])
        assert resp.json()["page_count"] == 31
        assert resp.json()["total_count"] == 310
        page += 1
        for doc in resp.json()["data"]:
            print(doc["message"])
        if page >= resp.json()["page_count"]:
            break
    data = [i.split("\n") for i in body.split("\n\n") if i]
    logs = [json.loads(i[1][6:]) for i in data if i[0].endswith("log")]
    assert 300 == sum([1 for i in logs if i["message"].startswith("hello")])
    #proc = [i["postproc"] for i in logs]
    #assert False in proc
    #assert True in proc


async def test_job_list(core4api, worker, mongodb):
    worker.start(1)
    worker.stop()
    await core4api.login()

    resp = await core4api.get('/core4/api/v1/job/list', request_timeout=120.)
    assert resp.code == 200
    pprint(resp.json())



async def test_error(core4api, worker):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.ErrorJob", "follow": True},
        request_timeout=120.
    )
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    print(">>>")
    pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
    print(">>>")
    pprint([(i["state"], i["trial"], i["attempts_left"]) for i in states])
    worker.stop()
    assert sum([1 for i in logs if "start execution" in i["message"]]) == 3
    assert sum([1 for i in logs if "done execution with [failed]" in i["message"]]) == 2
    assert sum([1 for i in logs if "done execution with [error]" in i["message"]]) == 1


class MyJob5(CoreJob):
    author = "mra"
    defer_time = 3
    defer_max = 20

    def execute(self):
        self.logger.info("trial [%d]", self.trial)
        self.defer("not, yet")

async def test_defer1(core4api, worker):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob5", "follow": True},
        request_timeout=120.
    )
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    print(">>>")
    pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
    print(">>>")
    pprint([(i["state"], i["trial"], i["attempts_left"]) for i in states])
    worker.stop()
    assert 'running' in set(sorted(set([i["state"] for i in states])))
    assert 'deferred' in set(sorted(set([i["state"] for i in states])))
    assert 'inactive' in set(sorted(set([i["state"] for i in states])))


class MyJob6(CoreJob):
    author = "mra"
    defer_time = 3
    defer_max = 30

    def execute(self):
        self.logger.info("trial [%d]", self.trial)
        if self.trial > 2:
            return
        self.defer("not, yet")

async def test_defer2(core4api, worker):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.MyJob6", "follow": True},
        request_timeout=120.
    )
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    print(">>>")
    pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
    print(">>>")
    pprint([(i["state"], i["trial"], i["attempts_left"]) for i in states])
    worker.stop()
    assert 'running' in set(sorted(set([i["state"] for i in states])))
    assert 'deferred' in set(sorted(set([i["state"] for i in states])))
    assert 'complete' in set(sorted(set([i["state"] for i in states])))


class ZeroJob(CoreJob):

    author = "mra"

    def execute(self, **kwargs):
        print(1/0.)

async def test_syntax_error(core4api, worker):
    worker.start(1)
    await core4api.login()

    resp = await core4api.post(
        '/core4/api/v1/job',
        json={"qual_name": "tests.api.test_job2.ZeroJob", "follow": True},
        request_timeout=120.
    )
    assert resp.code == 200
    states, logs = parse_sse(resp.body)
    print(">>>")
    pprint(["{} - {}".format(i["mode"], i["message"]) for i in logs])
    print(">>>")
    pprint([(i["state"], i["trial"], i["attempts_left"]) for i in states])
    worker.stop()
    assert 'running' in set(sorted(set([i["state"] for i in states])))
    assert 'error' in set(sorted(set([i["state"] for i in states])))


