import multiprocessing

import pytest
import requests
import time
import tornado.gen
from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.queue.job import JobPost
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.api.v1.tool import serve
from tests.api.test_response import setup

_ = setup


class StopHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.logger.warning("stop IOLoop now: %s", IOLoop.current())
        IOLoop.current().stop()


class CoreApiTestServer1(CoreApiContainer):
    enabled = True
    rules = (
        (r'/kill', StopHandler),
        (r'/static1', CoreStaticFileHandler, {"path": "static1"}),
        (r'/roles/?(.*)', RoleHandler),
        (r'/enqueue', JobPost),
    )


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
        if "token" in kwargs:
            token = kwargs.pop("token")
            if token is not None:
                kwargs.setdefault("headers", {})[
                    "Authorization"] = "Bearer " + token
            return requests.request(method, self.url(url), **kwargs)
        else:
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


def add_user(http, username):
    rolename = "role_" + username
    # rv = http.post("/tests/roles", json={"name": rolename,
    #                                      "perm": ["api://core4.api.v1.*"]})
    # assert rv.status_code == 200
    rv = http.post("/tests/roles",
                   json={
                       "name": username,
                       "role": ["user"],
                       "email": username + "@mail.com",
                       "password": username
                   })
    assert rv.status_code == 200
    conn = http.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username,
        token=None)
    assert conn.status_code == 200
    return conn.json()["data"]["token"]


def test_server_test(http):
    rv = http.get("/core4/api/v1/profile")
    assert rv.status_code == 200
    token = add_user(http, "user1")
    rv = http.get("/core4/api/v1/profile", token=token)
    assert rv.status_code == 200
    rv = http.get("/tests/roles", token=token)
    assert rv.status_code == 401
    rv = http.get("/tests/enqueue", token=token)
    assert rv.status_code == 401


if __name__ == '__main__':
    serve(CoreApiTestServer1)
