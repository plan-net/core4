import json
import logging
import os
import threading
import urllib.parse
from contextlib import closing
from http.cookies import SimpleCookie

import pymongo
import pytest
import time
import tornado.simple_httpclient
from tornado import httpclient

import core4.queue.worker
from core4.api.v1.tool.serve import CoreApiServerTool


class Worker:
    """
    Wraps :class:`core4.queue.worker.CoreWorker` to instantiate, start and
    stop a worker thread. See :func:`worker`.
    """
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

    def stop(self):
        for worker in self.worker:
            worker.exit = True
        for t in self.pool:
            t.join()

    def find_job(self, **kwargs):
        time.sleep(1)  # give the worker thread some time
        return core4.queue.helper.functool.find_job(**kwargs)


@pytest.fixture
def worker():
    """
    pytest fixture providing a core4 worker
    """
    w = Worker()
    w.start()
    yield w
    w.stop()


@pytest.fixture
def tearup(tmpdir, mongo_url="mongodb://core:654321@testmongo:27017",
           dbname="core4_test"):
    """
    pytest fixture to setup and teardown core4 database and configuration.
    """
    logging.shutdown()
    core4.logger.mixin.CoreLoggerMixin.completed = False
    dirname = os.path.dirname(__file__)
    os.environ["CORE4_CONFIG"] = os.path.join(dirname, "empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = mongo_url
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = dbname
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_logging__stderr"] = "DEBUG"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 60"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool True"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "foobar"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    os.environ["CORE4_OPTION_worker__max_cpu"] = "!!int 100"
    conn = pymongo.MongoClient(mongo_url)
    conn.drop_database(dbname)
    core4.logger.mixin.logon()
    yield
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    core4.util.tool.Singleton._instances = {}
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


class HTTPTestServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
    """
    Wraps a HTTP client/server.
    """
    def initialize(self, *, http_server=None, port=None):
        super().initialize()
        self._http_server = http_server
        self._http_port = port
        self.token = None
        self.admin_token = None

    async def login(self, username="admin", password="hans", code=200):
        """
        login the passed username, defaults to admin user
        """
        self.token = None
        resp = await self.get(
            "/core4/api/v1/login?username={}&password={}".format(
                username, password
            ))

        assert resp.code == code
        if code == 200:
            self.token = resp.json()["data"]["token"]
            if username == "admin":
                self.admin_token = self.token

    def set_admin(self):
        self.token = self.admin_token

    def post(self, path, body="", **kwargs):
        return self._fetch("POST", path=path, body=body, **kwargs)

    def put(self, path, body="", **kwargs):
        return self._fetch("PUT", path=path, body=body, **kwargs)

    def get(self, path, **kwargs):
        return self._fetch("GET", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._fetch("DELETE", path=path, **kwargs)

    async def _fetch(self, method, path, **kwargs):
        headers = kwargs.get("headers", {})
        if self.token:
            headers["Authorization"] = "bearer " + self.token
        kwargs["headers"] = headers
        if "body" in kwargs:
            body = kwargs["body"]
            if isinstance(body, dict):
                body = json.dumps(body)
            kwargs["body"] = body
        if "json" in kwargs:
            body = kwargs.pop("json")
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"
            kwargs["body"] = body
        req = httpclient.HTTPRequest(
            self.get_url(path), method=method, **kwargs)
        resp = await super().fetch(req, raise_error=False)
        return self._postproc(resp)

    def _postproc(self, response):

        def _json():
            return json.loads(response.body.decode("utf-8"))

        def _cookie():
            cookie = SimpleCookie()
            s = response.headers.get("set-cookie")
            cookie.load(s)
            return cookie

        response.json = _json
        response.cookie = _cookie
        response.ok = response.code == 200
        return response

    def get_url(self, path):
        p, *q = path.split("?")
        elems = urllib.parse.parse_qs("?".join(q))
        if q:
            p += "?" + urllib.parse.urlencode(elems, doseq=True)
        url = "http://127.0.0.1:%s%s" % (self._http_port, p)
        return url


def run_server(*app):
    loop = tornado.ioloop.IOLoop().current()
    http_server_port = tornado.testing.bind_unused_port()[1]
    serve = CoreApiServerTool()
    server = serve.create_routes(*app, port=http_server_port, core4api=True)
    serve.init_callback()

    with closing(HTTPTestServerClient(http_server=server,
                                      port=http_server_port)) as client:
        yield client

    serve.unregister()
    server.stop()

    if hasattr(server, "close_all_connections"):
        loop.run_sync(
            server.close_all_connections
        )
