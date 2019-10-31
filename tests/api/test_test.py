import json
import logging
import os
import urllib.parse
from contextlib import closing
from http.cookies import SimpleCookie

import pymongo
import pytest
import tornado.gen
import tornado.ioloop
import tornado.simple_httpclient
import tornado.web
from tornado import httpclient

import core4.logger.mixin
from core4.api.v1.server import CoreApiServer
from core4.api.v1.tool.serve import CoreApiServerTool


MONGO_URL = 'mongodb://core:654321@testmongo:27017'
MONGO_DATABASE = 'core4test'
ASSET_FOLDER = '../asset'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture(autouse=True)
def setup(tmpdir):
    logging.shutdown()
    core4.logger.mixin.CoreLoggerMixin.completed = False
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 60"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool True"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    yield
    conn.drop_database(MONGO_DATABASE)
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


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)[MONGO_DATABASE]


class HTTPTestServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
    def initialize(self, *, http_server=None, port=None):
        super().initialize()
        self._http_server = http_server
        self._http_port = port
        self.token = None
        self.admin_token = None

    async def login(self, username="admin", password="hans"):
        self.token = None
        resp = await self.get(
            "/core4/api/v1/login?username={}&password={}".format(
                username, password
            ))
        assert resp.code == 200
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
        print(url)
        return url


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")


@pytest.yield_fixture
def tornado_test():
    yield from run(
        tornado.web.Application([(r"/test", MainHandler)])
    )


@pytest.yield_fixture
def core4api():
    yield from run(
        CoreApiServer
    )


def run(*app):
    loop = tornado.ioloop.IOLoop().current()
    http_server_port = tornado.testing.bind_unused_port()[1]
    serve = CoreApiServerTool()
    server = serve.create_routes(*app, port=http_server_port, core4api=False)
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


async def test_core4_server1(core4api):
    resp = await core4api.get(
        '/core4/api/v1/login?username=admin&password=hans')
    assert resp.code == 200


async def test_core4_server2(core4api):
    resp = await core4api.get(
        '/core4/api/v1/login?username=admin&password=hans')
    print(core4api.get_url("/"))
    assert resp.code == 200


async def test_core4_server3(core4api):
    URL = '/core4/api/v1/login'
    resp = await core4api.get(URL + '?username=admin&password=hans')
    print(core4api.get_url("/"))
    assert resp.code == 200
    resp = await core4api.post(
        URL, body='{"username": "admin", "password": "hans"}')
    assert resp.code == 200

async def test_core4_server4(core4api):
    URL = '/core4/api/v1/login'
    resp = await core4api.get(URL + '?username=admin&password=hans')
    assert resp.code == 200
    cookie = list(resp.cookie().values())
    header = {"Cookie": "token=" + cookie[0].coded_value}
    resp = await core4api.get(URL, headers=header)
    assert resp.code == 200

