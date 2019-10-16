import pytest
import tornado
import tornado.simple_httpclient
import tornado.httpserver
import tornado.web
import json
from .tornado_test import run


class MainHandler1(tornado.web.RequestHandler):
    async def get(self):
        self.finish(json.dumps({"hello": "world"}))


class MainHandler2(MainHandler1):
    async def post(self):
        payload = json.loads(self.request.body.decode("utf-8"))
        self.finish(json.dumps(payload))


@pytest.yield_fixture
def server1():
    yield from run(
        tornado.web.Application([(r"/hello", MainHandler1)])
    )


@pytest.yield_fixture
def server2():
    yield from run(
        tornado.web.Application([
            (r"/hello1", MainHandler1),
            (r"/hello2", MainHandler2)
        ]),
    )


async def test_server1(server1):
    ret = await server1.get("/hello")
    assert ret.code == 200
    assert ret.json() == {"hello": "world"}


async def test_server2(server2):
    ret = await server2.get("/hello1")
    assert ret.json() == {"hello": "world"}
    ret = await server2.post("/hello2", json={"value": "0815"})
    assert ret.code == 200
    assert ret.json() == {'value': '0815'}
