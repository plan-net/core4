import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from .conftest import run_server
from core4.queue.job import CoreJob
from core4.queue.helper.functool import enqueue


# This example uses automatic setup/teardown

@pytest.fixture(autouse=True)
def setup(tearup):
    pass


class Handler(CoreRequestHandler):

    async def get(self):
        self.reply(True)


class Container(CoreApiContainer):

    root = "/abc"

    rules = [
        ("/def", Handler)
    ]


@pytest.fixture
def api():
    yield from run_server(
        Container
    )

async def test_http(api):
    await api.login()
    resp = await api.get("/abc/def")
    assert resp.code == 200
    assert resp.ok
    resp.body
    resp.json()
    dict(resp.headers)
    resp.cookie()

    resp = await api.get("/abc/xxx")
    assert resp.code == 404
    assert not resp.ok


class MyJob(CoreJob):
    author = "mra"

    def execute(self, n=5, sleep=5, **kwargs):
        for i in range(n):
            enqueue("core4.queue.helper.job.example.DummyJob", sleep=sleep, i=i)


async def test_worker(api, worker):

    def callback(chunk):
        for line in chunk.decode("utf-8").split("\n"):
            if line.startswith("event: "):
                event = line[len("event: "):]
                print(event)

    await api.login()
    resp = await api.post("/core4/api/v1/job", json={
        "qual_name": MyJob.qual_name(),
        "args": {"n": 10, "sleep": 5},
        "follow": True
    }, streaming_callback=callback, request_timeout=360)
    assert resp.ok

    # since MyJob launches additional jobs we should wait until sys.queue
    # is empty before exiting the test and stopping the worker

    while True:
        ret = worker.find_job()
        print(len(ret))
        if not ret:
            break
