import logging
import multiprocessing
import os

import pymongo
import pytest
import requests
import time
from tornado.ioloop import IOLoop

import core4.api.v1.util
import core4.logger
import core4.queue.main
import core4.queue.worker
import core4.service.setup
import core4.util
import core4.util.tool
from core4.api.v1.application import CoreApiServerTool, CoreApiContainer, serve
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.queue.job import JobPost
#from core4.api.v1.request.queue.job import JobSummary
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import QueueStatus
from tests.util import asset

ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


@pytest.fixture(autouse=True)
def setup(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 60"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool False"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    setup = core4.service.setup.CoreSetup()
    setup.make_role()
    yield
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

@pytest.fixture
def app():
    return CoreApiServerTool().make_routes(MyApp)


@pytest.fixture(autouse=True)
def reset():
    core4.logger.mixin.logon()


@pytest.fixture()
def queue():
    return core4.queue.main.CoreQueue()


def json_decode(resp):
    return core4.api.v1.util.json_decode(resp.body.decode("utf-8"))


class StopHandler(CoreRequestHandler):

    def get(self):
        self.logger.warning("stop IOLoop now")
        IOLoop.current().stop()


class LocalTestServer:

    base_url = "/core4/api/v1"

    def __init__(self):
        self.port = 5555
        self.process = None
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        while True:
            try:
                requests.get(self.url("/profile"), timeout=1)
                break
            except:
                pass
            time.sleep(1)
        self.signin = requests.get(
            self.url("/login?username=admin&password=hans"))
        self.token = self.signin.json()["data"]["token"]
        assert self.signin.status_code == 200

    def url(self, url):
        return "http://localhost:{}{}".format(self.port, self.base_url) + url

    def request(self, method, url, **kwargs):
        kwargs.setdefault("headers", {})[
            "Authorization"] = "Bearer " + self.token
        return requests.request(method, self.url(url), **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def run(self):

        pubs = QueueStatus()
        IOLoop.current().spawn_callback(pubs.update)
        cls = self.start(publisher=pubs)
        cls.root = self.base_url
        self.serve(cls)

    def serve(self, cls, **kwargs):
        serve(cls, port=self.port, **kwargs)

    def start(self, *args, **kwargs):

        class CoreApiTestServer(CoreApiContainer):
            rules = [
                (r'/queue', QueueHandler, dict(
                    source=kwargs.get("publisher"))),
                #(r'/jobs/summary', JobSummary),
                (r'/jobs/poll/?(.*)', JobStream),
                (r'/jobs/?(.*)', JobHandler),
                (r'/enqueue', JobPost),
                (r'/kill', StopHandler)
            ]
        return CoreApiTestServer

    def stop(self):
        rv = self.get("/kill")
        assert rv.status_code == 200
        self.process.join()


@pytest.fixture()
def http():
    return LocalTestServer()


def test_server_test(http):
    rv = http.get("/profile")
    assert rv.status_code == 200
    http.stop()


def test_enqueue(http, queue):
    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=1))
    assert rv.status_code == 200
    job_id = rv.json()["data"]["_id"]
    worker = core4.queue.worker.CoreWorker()
    worker.work_jobs()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    rv = http.get("/jobs/" + job_id)
    assert rv.status_code == 200
    assert rv.json()["data"]["runtime"] >= 1.0
    assert rv.json()["data"]["state"] == "complete"
    assert rv.json()["data"]["args"] == {"sleep": 1}
    http.stop()


def test_async_enqueue(http, queue):
    worker = core4.queue.worker.CoreWorker()
    t = multiprocessing.Process(target=worker.start, name="test-worker-1")
    t.start()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    rv = http.post(
        "/jobs/poll", json=dict(name="core4.queue.helper.DummyJob", sleep=3),
        stream=True)
    assert rv.status_code == 200
    states = []
    for line in rv.iter_lines():
        if line:
            data = core4.api.v1.util.json_decode(line.decode("utf-8"))
            if data:
                state = data.get("state")
                states.append(state)
    assert states[0] == "pending"
    assert set(states[1:-1]) == {"running"}
    assert states[-1] == "complete"
    #assert states[-1] is None
    queue.halt(now=True)
    t.join()
    http.stop()


def test_queue(http, queue):
    worker = core4.queue.worker.CoreWorker()
    t = multiprocessing.Process(target=worker.start, name="test-worker-1")
    t.start()
    while queue.config.sys.queue.count_documents({}) > 0:
        time.sleep(1)
    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=5))
    assert rv.status_code == 200
    rv = http.get("/queue", stream=True)
    assert rv.status_code == 200
    states = []
    for line in rv.iter_lines():
        data = core4.api.v1.util.json_decode(line.decode("utf-8"))
        if data:
            states.append(sorted(list(data.keys())))
            if list(data.keys()) == ["timestamp"]:
                break
    queue.halt(now=True)
    t.join()
    http.stop()
    assert states == [['pending', 'timestamp'],
                      ['running', 'timestamp'],
                      ['timestamp']]


def test_getter(http, queue):
    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=5))
    assert rv.status_code == 200
    j1 = rv.json()["data"]["_id"]
    rv = http.get("/jobs")
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 1
    assert rv.json()["data"][0]["state"] == "pending"

    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=4))
    assert rv.status_code == 200
    j2 = rv.json()["data"]["_id"]

    rv = http.get("/jobs")
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 2
    assert rv.json()["data"][0]["state"] == "pending"
    assert rv.json()["data"][1]["state"] == "pending"

    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=4))
    assert rv.status_code == 400

    rv = http.get("/jobs")
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 2
    act = [i["_id"] for i in rv.json()["data"]]
    assert sorted(act) == sorted([j1, j2])

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"

    http.stop()

def test_flag(http, queue):
    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=5))
    assert rv.status_code == 200
    j1 = rv.json()["data"]["_id"]
    rv = http.delete("/jobs")
    assert rv.status_code == 400

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["removed_at"] is None

    rv = http.delete("/jobs/" + j1)
    assert rv.status_code == 200

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["removed_at"] is not None

    rv = http.put("/jobs/kill/" + j1)
    assert rv.status_code == 200

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["killed_at"] is not None

    http.stop()

import core4.queue.job

class ErrorJob(core4.queue.job.CoreJob):
    author = "mra"

    def execute(self, *args, **kwargs):
        raise RuntimeError("expected failure")

def test_restart_error(http, queue):
    rv = http.post(
        "/enqueue", json=dict(name="tests.api.test_job.ErrorJob", sleep=5))
    assert rv.status_code == 200
    j1 = rv.json()["data"]["_id"]

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["removed_at"] is None

    worker = core4.queue.worker.CoreWorker()
    worker.work_jobs()

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        if rv.json()["data"]["state"] == "error":
            break

    rv = http.put("/jobs/" + j1 + "?action=restart")
    assert rv.status_code == 200
    j2 = rv.json()["data"]["new_id"]

    rv2 = http.get("/jobs/" + j2)
    assert rv2.status_code == 200
    assert rv2.json()["data"]["state"] == "pending"
    assert rv2.json()["data"]["_id"] == j2
    assert rv2.json()["data"]["enqueued"]["parent_id"] == j1

    rv3 = http.get("/jobs/" + j1)
    assert rv3.status_code == 200
    assert rv3.json()["data"]["state"] == "error"
    assert rv3.json()["data"]["_id"] == j1
    assert rv3.json()["data"]["enqueued"]["child_id"] == j2

    http.stop()


def test_kill(http, queue):

    worker = core4.queue.worker.CoreWorker()
    t = multiprocessing.Process(target=worker.start, name="test-worker-1")
    t.start()

    rv = http.post(
        "/enqueue", json=dict(name="core4.queue.helper.DummyJob", sleep=600))
    assert rv.status_code == 200
    j1 = rv.json()["data"]["_id"]

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["removed_at"] is None

    rv = http.put("/jobs/" + j1 + "?action=xxx")
    assert rv.status_code == 400

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        if rv.json()["data"]["state"] == "running":
            break

    rv = http.put("/jobs/" + j1 + "?action=kill")
    assert rv.status_code == 200

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        if rv.json()["data"]["state"] == "killed":
            break

    rv = http.put("/jobs/" + j1 + "?action=delete")
    assert rv.status_code == 200

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        if rv.json()["data"]["journal"]:
            break

    queue.halt(now=True)
    t.join()
    http.stop()

class DeferJob(core4.queue.job.CoreJob):
    author = "mra"
    defer_time = 600
    defer_max = 6000

    def execute(self, *args, **kwargs):
        self.defer("expected defer")

def test_restart_deferred(http, queue):

    worker = core4.queue.worker.CoreWorker()
    t = multiprocessing.Process(target=worker.start, name="test-worker-1")
    t.start()

    rv = http.post(
        "/enqueue", json=dict(name="tests.api.test_job.DeferJob"))
    assert rv.status_code == 200
    j1 = rv.json()["data"]["_id"]

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["state"] == "pending"
    assert rv.json()["data"]["removed_at"] is None

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        if rv.json()["data"]["state"] == "deferred":
            break

    rv = http.get("/jobs/" + j1)
    assert rv.status_code == 200
    assert rv.json()["data"]["trial"] == 1

    rv = http.put("/jobs/" + j1 + "?action=restart")
    assert rv.status_code == 200

    while True:
        rv = http.get("/jobs/" + j1)
        assert rv.status_code == 200
        data = rv.json()["data"]
        if data["trial"] == 2 and data["state"] == "deferred":
            break

    queue.halt(now=True)
    t.join()
    http.stop()
