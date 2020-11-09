import json
import threading
from pprint import pprint
import pytest
import time
from bson.objectid import ObjectId

import core4.api.v1.request.role.field
import core4.queue.helper.job.example
import core4.queue.main
import core4.util.crypt
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.role.main import CoreRole
from core4.api.v1.server import CoreApiServer, CoreApiContainer
from tests.api.test_test import setup, mongodb, core4api, run

_ = setup
_ = mongodb
_ = core4api


class WorkerHelper:
    def __init__(self):
        self.queue = core4.queue.main.CoreQueue()
        self.pool = []
        self.worker = []

    def start(self, num=1):
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


async def test_login(core4api):
    await core4api.login()
    resp = await core4api.get(
        '/core4/api/v1/profile')
    assert resp.code == 200


async def test_post(core4api, worker):
    worker.start()
    await core4api.login()
    data = {
        "name": "core4.queue.helper.job.example.DummyJob"
    }
    resp = await core4api.post('/core4/api/v1/jobs/enqueue', json=data)
    assert resp.code == 200
    worker.wait_queue()
    assert resp.json()["data"][
               "name"] == "core4.queue.helper.job.example.DummyJob"


class MyJob(core4.queue.helper.job.example.DummyJob):
    author = "mra"

    def execute(self):
        for i in range(50):
            self.logger.info("message {}".format(i + 1))
            time.sleep(0.1)


def test_find_job():
    print(MyJob.qual_name())


async def test_poll(core4api, worker):
    worker.start()
    await core4api.login()
    data = {
        # "name": "core4.queue.helper.job.example.DummyJob"
        "name": "tests.api.test_job.MyJob"
    }
    resp = await core4api.post('/core4/api/v1/jobs/poll', json=data)
    assert resp.code == 200
    worker.wait_queue()
    event = []
    for ev in resp.body.decode("utf-8").split("\n\n"):
        typ, *data = ev.split("\n")
        if typ:
            event.append({"type": typ, "data": json.loads("\n".join(data)[6:])})
    logs = [i["data"] for i in event if i["type"] == "event: log"]
    close = [i["data"] for i in event if i["type"] == "event: close"]
    tests = [i for i in logs if i["message"].startswith("message")]
    assert len(tests) == 50
    states = [i["data"] for i in event if i["type"] == "event: state"]
    assert states[-1]["state"] == "complete"
    assert len(close) == 1
    # obsolete because you cannot be sure that the last event is not a log event
    #assert event[-1]["type"] == "event: close"
    #assert event[-1]["data"] == {}


class MyJobHandler(JobStream):
    author = "mra"
    title = "job enqueue"

    async def post(self):
        ret = await self.enqueue(core4.queue.helper.job.example.DummyJob)
        self.reply(ret._id)


async def test_enqueue_permission(core4api, worker):
    role = CoreRole(
        name="job_access",
        realname="Michael Rau",
        is_active=True,
        perm=[
            "job://core4.queue.helper.job.example.DummyJob/x",
            "api://core4.api.v1.request.queue.*",
        ]
    )
    await role.save()
    role._check_user()
    assert not role.is_user
    user = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=True,
        email="m.rau@plan-net.com",
        password="hello world",
        role=["job_access"]
    )
    await user.save()
    user._check_user()
    assert user.is_user
    core4.util.crypt.pwd_context.verify("hello world", role.password)
    role.password = "very secret"

    # worker.start()
    #
    await core4api.login("mra", "hello world")
    data = {
        "name": "core4.queue.helper.job.example.DummyJob"
    }
    resp = await core4api.post('/core4/api/v1/jobs/enqueue', json=data)
    assert resp.code == 200


class MyCoreApiServer(CoreApiContainer):
    root = "/another"
    rules = [
        (r'/test', MyJobHandler),
    ]


@pytest.yield_fixture
def mycore4api():
    yield from run(
        CoreApiServer,
        MyCoreApiServer
    )


async def test_enqueue_by_api_permission(mycore4api, worker):
    role = CoreRole(
        name="job_access",
        realname="Michael Rau",
        is_active=True,
        perm=[
            "job://core4.queue.helper.job.example.DummyJob/x",
            "api://core4.api.v1.request.queue.*",
            "api://tests.api.test_job.*",
        ]
    )
    await role.save()
    role._check_user()
    assert not role.is_user
    user = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=True,
        email="m.rau@plan-net.com",
        password="hello world",
        role=["job_access"]
    )
    await user.save()
    user._check_user()
    assert user.is_user
    core4.util.crypt.pwd_context.verify("hello world", role.password)
    role.password = "very secret"

    # worker.start()
    #
    await mycore4api.login("mra", "hello world")
    resp = await mycore4api.post('/another/test')
    assert resp.code == 200
    oid = ObjectId(resp.json()["data"])


async def test_job_listing(core4api, worker):
    worker.start()
    role = CoreRole(
        name="job_access",
        realname="Michael Rau",
        is_active=True,
        perm=[
            "job://core4.queue.helper.job.example.DummyJob/x",
            "api://core4.api.v1.request.queue.*",
            "api://tests.api.test_job.*",
        ]
    )
    await role.save()
    role._check_user()
    assert not role.is_user
    user = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=True,
        email="m.rau@plan-net.com",
        password="hello world",
        role=["job_access"]
    )
    await user.save()
    user._check_user()
    assert user.is_user
    while True:
        if worker.worker[0].phase.get("loop", None) is not None:
            break
        time.sleep(0.5)
    await core4api.login("mra", "hello world")

    rv = await core4api.get("/core4/api/v1/jobs/list?q=core4")
    assert rv.code == 200
    print([j["_id"] for j in rv.json()["data"]])

    rv = await core4api.get('/core4/api/v1/jobs/list?filter={"name": "core4.util.email.RoleEmail"}')
    assert rv.code == 200
    print([j["_id"] for j in rv.json()["data"]])

    #worker.wait_queue()


