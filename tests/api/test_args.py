import json

import datetime
import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.server import CoreApiServer
from tests.api.test_test import run, setup

_ = setup


class MainHandler(CoreRequestHandler):
    author = "mra"

    def get(self):
        a = self.get_argument("a", as_type=int)
        self.reply(dict(
            a=a
        ))


class BadBodyHandler(CoreRequestHandler):
    author = "mra"

    def post(self):
        self.reply("hello world")


class ArgsHandler(CoreRequestHandler):
    author = "mra"

    def get(self):
        ret = {}
        a1 = self.get_argument("a1", default=None)
        ret["a1"] = "%s = %s" % (type(a1), a1)
        a2 = self.get_argument("a2", default=None, as_type=int)
        ret["a2"] = "%s = %s" % (type(a2), a2)
        # a3 = self.get_arguments("a3")
        # ret["a3"] = "%s = %s" %(type(a3), a3)
        # a4 = self.get_arguments("a4", as_type=int)
        # ret["a4"] = "%s = %s" %(type(a4), a4)
        a5 = self.get_argument("a5", as_type=bool, default=False)
        ret["a5"] = "%s = %s" % (type(a5), a5)
        a6 = self.get_argument("a6", as_type=float, default=None)
        ret["a6"] = "%s = %s" % (type(a6), a6)
        a7 = self.get_argument("a7", as_type=dict, default={})
        ret["a7"] = "%s = %s" % (type(a7), json.dumps(a7, sort_keys=True))
        a8 = self.get_argument("a8", as_type=datetime.datetime, default=None)
        ret["a8"] = "%s = %s" % (type(a8), a8)
        self.reply(ret)

    def post(self):
        self.get()


class ContainerTest(CoreApiContainer):
    root = "/test"
    rules = [
        ("/abc", MainHandler),
        ("/bad", BadBodyHandler),
        ("/args", ArgsHandler)
    ]


@pytest.yield_fixture
def core4_test():
    yield from run(
        CoreApiServer,
        ContainerTest
    )


async def test_login(core4_test):
    await core4_test.login()
    resp = await core4_test.get(
        '/core4/api/v1/profile')
    assert resp.code == 200


async def test_args(core4_test):
    await core4_test.login()
    resp = await core4_test.get(
        '/core4/api/v1/profile')
    assert resp.code == 200

    resp = await core4_test.get('/test/abc')
    assert resp.code == 400
    assert "missing argument" in resp.json()["error"].lower()

    resp = await core4_test.get('/test/abc?a=b')
    assert resp.code == 400
    assert "as_type [int]" in resp.json()["error"].lower()

    resp = await core4_test.get('/test/abc?a=1')
    assert resp.code == 200


async def test_bad_body(core4_test):
    await core4_test.login()

    resp = await core4_test.post('/test/bad', body="hello world")
    assert resp.code == 200

    resp = await core4_test.post('/test/bad', body='{"a": , 123}')
    assert resp.code == 200

    resp = await core4_test.post('/test/bad', body='{"a": 123}')
    assert resp.code == 200

    resp = await core4_test.post('/test/bad', body=b'3\xab Floppy (A).link')
    assert resp.code == 200


async def test_query_args(core4_test):
    await core4_test.login()

    rv = await core4_test.get("/test/args")
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"

    rv = await core4_test.get("/test/args?a1=123")
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 123"

    rv = await core4_test.get("/test/args?a2=123")
    assert rv.code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    rv = await core4_test.get("/test/args?a2=123.456")
    assert rv.code == 400

    rv = await core4_test.get("/test/args?a1=123&a1=456")
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 456"

    # out of scope since get_arguments is out of scope
    # rv = core4_test.get("/test/args?a3=123&a3=456")
    # assert rv.code == 200
    # assert rv.json()["data"]["a3"] == "<class 'list'> = ['123', '456']"
    # print(rv.json()["data"])

    # out of scope since get_arguments is out of scope
    # rv = core4_test.get("/test/args?a4=123&a4=456")
    # assert rv.code == 200
    # #print(rv.json()["data"]["a4"])
    # assert rv.json()["data"]["a4"] == "<class 'list'> = [123, 456]"

    rv = await core4_test.get("/test/args?a5=y")
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = await core4_test.get("/test/args?a5=0")
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    rv = await core4_test.get("/test/args?a5=on")
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = await core4_test.get("/test/args?a5=off")
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    rv = await core4_test.get("/test/args?a5=T")
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = await core4_test.get("/test/args?a5=xyz")
    assert rv.code == 400
    assert 'parameter [a5] expected as_type [bool]' in rv.json()["error"]

    rv = await core4_test.get("/test/args?a6=123.456")
    assert rv.code == 200
    assert rv.json()["data"]["a6"] == "<class 'float'> = 123.456"

    rv = await core4_test.get('/test/args?a7={"a": 123, "b": "hello"}')
    assert rv.code == 200
    assert rv.json()["data"][
               "a7"] == "<class 'dict'> = {\"a\": 123, \"b\": \"hello\"}"

    rv = await core4_test.get('/test/args?a8=2018-2-01')
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 00:00:00"

    rv = await core4_test.get('/test/args?a8=2018-2-01T12:34:55')
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 12:34:55"

    rv = await core4_test.get('/test/args?a8=2009-01-01T12:55:12')
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2009-01-01 12:55:12"


async def test_json_args(core4_test):
    await core4_test.login()

    rv = await core4_test.post("/test/args")
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"

    rv = await core4_test.post("/test/args", body={"a1": "123"})
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 123"

    rv = await core4_test.post("/test/args", body={"a2": 123})
    assert rv.code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    # behavior is different to query parameter
    rv = await core4_test.post("/test/args", body={"a2": 123.456})
    assert rv.code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    # behavior is different to query parameter
    rv = await core4_test.post("/test/args", body={"a1": "123", "a1": "456"})
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 456"

    # rv = await core4_test.get("/test/args?a4=123&a4=456")
    # assert rv.code == 200
    # # print(rv.json()["data"]["a4"])
    # assert rv.json()["data"]["a4"] == "<class 'list'> = [123, 456]"

    rv = await core4_test.post("/test/args", body={"a5": True})
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = await core4_test.post("/test/args", body={"a5": False})
    assert rv.code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = await core4_test.get("/test/args?a5=0")
    # assert rv.code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = await core4_test.get("/test/args?a5=on")
    # assert rv.code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = True"
    #
    # behavior is different to query parameter
    # rv = await core4_test.get("/test/args?a5=off")
    # assert rv.code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = await core4_test.get("/test/args?a5=T")
    # assert rv.code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = await core4_test.post("/test/args", body={"a5": "xyz"})
    assert rv.code == 400
    assert 'parameter [a5] expected as_type [bool]' in rv.json()["error"]

    rv = await core4_test.post("/test/args", body={"a6": 123.456})
    assert rv.code == 200
    assert rv.json()["data"]["a6"] == "<class 'float'> = 123.456"

    rv = await core4_test.post("/test/args",
                               body={"a7": {"b": "hello", "a": 123}})
    assert rv.code == 200
    assert rv.json()["data"][
               "a7"] == "<class 'dict'> = {\"a\": 123, \"b\": \"hello\"}"

    rv = await core4_test.post("/test/args", body={"a8": '2018-2-01'})
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 00:00:00"

    rv = await core4_test.post("/test/args", body={"a8": '2018-2-01T12:34:55'})
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 12:34:55"

    rv = await core4_test.post("/test/args",
                               body={"a8": '2009-01-01T12:55:12'})
    assert rv.code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2009-01-01 12:55:12"


async def test_conv_error(core4_test):
    await core4_test.login()
    rv = await core4_test.post("/test/args")
    assert rv.code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"
    rv = await core4_test.get('/test/args?a8=9999-aa-bb')
    assert rv.code == 400
    assert "parameter [a8] expected as_type [datetime]" in rv.json()["error"]
