import threading

import pytest
import core4.queue.helper.job.example
import core4.api.v1.request.role.field
import core4.queue.main
from tests.api.test_test import setup, mongodb, core4api
import time
import json


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
    assert resp.json()["data"]["name"] == "core4.queue.helper.job.example.DummyJob"

class MyJob(core4.queue.helper.job.example.DummyJob):

    author = "mra"
    def execute(self):
        for i in range(50):
            self.logger.info("message {}".format(i+1))
            time.sleep(0.1)

def test_find_job():
    print(MyJob.qual_name())

async def test_poll(core4api, worker):
    worker.start()
    await core4api.login()
    data = {
        #"name": "core4.queue.helper.job.example.DummyJob"
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
    tests = [i for i in logs if i["message"].startswith("message")]
    assert len(tests) == 50
    states = [i["data"] for i in event if i["type"] == "event: state"]
    assert states[-1]["state"] == "complete"
    assert event[-1]["type"] == "event: close"
    assert event[-1]["data"] == {}