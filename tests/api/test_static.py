import multiprocessing
from pprint import pprint

import pytest
import requests
import time
import tornado.gen
from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.api.v1.tool.functool import serve
from tests.api.test_response import setup

_ = setup


class StopHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.logger.warning("stop IOLoop now: %s", IOLoop.current())
        IOLoop.current().stop()


class DownloadHandler(CoreRequestHandler):

    protected = False

    async def get(self):
        await self.download("./static1/asset/test.dat", "test.dat")


class StaticTest2(CoreStaticFileHandler):
    path = "static1"


class CoreApiTestServer1(CoreApiContainer):
    enabled = True
    rules = [
        (r'/kill', StopHandler),
        (r'/static1', CoreStaticFileHandler, {"path": "static1"}),
        (r'/static2', StaticTest2),
        (r'/public2', StaticTest2, {"protected": False}),
        (r'/download1', DownloadHandler),
    ]


class HttpServer:

    def __init__(self, *args):
        self.cls = args
        self.port = 5555
        self.process = None
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        while True:
            try:
                url = self.url("/core4/api/v1/profile")
                requests.get(url, timeout=1)
                break
            except:
                pass
            time.sleep(1)
            tornado.gen.sleep(1)
        self.signin = requests.get(
            self.url("/core4/api/v1/login?username=admin&password=hans"))
        self.token = self.signin.json()["data"]["token"]
        assert self.signin.status_code == 200

    def url(self, url):
        return "http://localhost:{}".format(self.port) + url

    def request(self, method, url, **kwargs):
        if self.token:
            kwargs.setdefault("headers", {})[
                "Authorization"] = "Bearer " + self.token
        return requests.request(method, self.url(url),
                                cookies=self.signin.cookies, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def run(self):
        serve(*self.cls, port=self.port)

    def stop(self):
        rv = self.get("/tests/kill")
        assert rv.status_code == 200
        self.process.join()


@pytest.fixture()
def http():
    server = HttpServer(CoreApiTestServer1)
    yield server
    server.stop()


def test_server_test(http):
    rv = http.get("/core4/api/v1/profile")
    assert rv.status_code == 200


def test_core_landing(http):
    rv = http.get("/")
    assert rv.status_code == 200
    rv = http.get("")
    assert rv.status_code == 200
    rv = http.get("/index.html")
    assert rv.status_code == 200
    rv = http.get("/default.html")
    assert rv.status_code == 404
    url = http.url("")
    rv = requests.get(url)
    assert rv.status_code == 200
    url = http.url("/favicon.ico")
    rv = requests.get(url)
    assert rv.status_code == 200


def test_static1(http):
    rv = http.get("/tests/static1/index.html")
    assert rv.status_code == 200
    doc1 = rv.content
    rv = http.get("/tests/static1/")
    assert rv.status_code == 200
    doc2 = rv.content
    rv = http.get("/tests/static1")
    assert rv.status_code == 200
    doc3 = rv.content
    assert doc1 == doc2 == doc3
    rv = http.get("/tests/static1index.html")
    assert rv.status_code == 404
    rv = http.get("/tests/static1/xxx/../index.html")
    assert rv.status_code == 200
    rv = http.get("/tests/static1/../test_static.py")
    assert rv.status_code == 403


def test_image(http):
    rv = http.get("/tests/static1/sub/test.html")
    assert rv.status_code == 200
    rv = http.get("/tests/static1/sub/../asset/head.png")
    assert rv.status_code == 200
    assert rv.content[:20] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00'
    rv = http.get("/favicon.ico")
    assert rv.status_code == 200


def test_css(http):
    rv = http.get("/tests/static1/index.html")
    assert rv.status_code == 200
    rv = http.get("/tests/static1/test.css")
    assert rv.status_code == 200
    pprint(rv.content)
    rv = http.get("/tests/static1/sub/test.html")
    assert rv.status_code == 200
    pprint(rv.content)


def test_class(http):
    url = http.url("/tests/static2")
    rv = requests.get(url)
    assert rv.status_code == 401
    rv = http.get("/tests/static2")
    assert rv.status_code == 200
    rv = http.get("/tests/static2/")
    assert rv.status_code == 200
    rv = http.get("/tests/static2/index.html")
    assert rv.status_code == 200
    rv = http.get("/tests/static2/sub/test.html")
    assert rv.status_code == 200
    rv = http.get("/tests/static2/sub/../test.css")
    assert rv.status_code == 200


def test_public_class(http):
    url = http.url("/tests/public2")
    rv = requests.get(url)
    assert rv.status_code == 200
    rv = http.get("/tests/public2")
    assert rv.status_code == 200
    rv = http.get("/tests/public2/")
    assert rv.status_code == 200
    rv = http.get("/tests/public2/index.html")
    assert rv.status_code == 200
    rv = http.get("/tests/public2/sub/test.html")
    assert rv.status_code == 200
    rv = http.get("/tests/public2/sub/../test.css")
    assert rv.status_code == 200


# def test_download(http):
#     url = http.url("/tests/download1")
#     rv = requests.get(url)
#     assert rv.status_code == 200


if __name__ == '__main__':
    # from core4.api.v1.tool import serve, serve_all
    # serve_all(filter=[
    #     "project.api",
    #     "core4.api.v1.server",
    #     "example"])
    serve(CoreApiTestServer1)
