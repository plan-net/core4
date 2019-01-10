import json

import datetime
import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.tool import serve
from core4.api.v1.request.main import CoreRequestHandler
from tests.api.test_response import setup, LocalTestServer, StopHandler

print(setup)


class ArgsHandler(CoreRequestHandler):

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


class CoreApiTestServer(CoreApiContainer):
    enabled = False
    rules = [
        (r'/kill', StopHandler),
        (r'/args', ArgsHandler)
    ]


class HttpServer(LocalTestServer):

    def start(self, *args, **kwargs):
        return CoreApiTestServer


@pytest.fixture()
def http():
    server = HttpServer()
    yield server
    server.stop()


def test_server_test(http):
    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200


def test_query_args(http):
    rv = http.get("/args")
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"

    rv = http.get("/args?a1=123")
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 123"

    rv = http.get("/args?a2=123")
    assert rv.status_code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    rv = http.get("/args?a2=123.456")
    assert rv.status_code == 400

    rv = http.get("/args?a1=123&a1=456")
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 456"

    # out of scope since get_arguments is out of scope
    # rv = http.get("/args?a3=123&a3=456")
    # assert rv.status_code == 200
    # assert rv.json()["data"]["a3"] == "<class 'list'> = ['123', '456']"
    # print(rv.json()["data"])

    # out of scope since get_arguments is out of scope
    # rv = http.get("/args?a4=123&a4=456")
    # assert rv.status_code == 200
    # #print(rv.json()["data"]["a4"])
    # assert rv.json()["data"]["a4"] == "<class 'list'> = [123, 456]"

    rv = http.get("/args?a5=y")
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = http.get("/args?a5=0")
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    rv = http.get("/args?a5=on")
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = http.get("/args?a5=off")
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    rv = http.get("/args?a5=T")
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = http.get("/args?a5=xyz")
    assert rv.status_code == 400
    assert 'parameter [a5] expected as_type [bool]' in rv.json()["error"]

    rv = http.get("/args?a6=123.456")
    assert rv.status_code == 200
    assert rv.json()["data"]["a6"] == "<class 'float'> = 123.456"

    rv = http.get('/args?a7={"a": 123, "b": "hello"}')
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a7"] == "<class 'dict'> = {\"a\": 123, \"b\": \"hello\"}"

    rv = http.get('/args?a8=2018-2-01')
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 00:00:00"

    rv = http.get('/args?a8=2018-2-01T12:34:55')
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 12:34:55"

    rv = http.get('/args?a8=2009-01-01T12:55:12 CET')
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2009-01-01 11:55:12"


def test_json_args(http):
    rv = http.post("/args")
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"

    rv = http.post("/args", json={"a1": "123"})
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 123"

    rv = http.post("/args", json={"a2": 123})
    assert rv.status_code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    # behavior is different to query parameter
    rv = http.post("/args", json={"a2": 123.456})
    assert rv.status_code == 200
    assert rv.json()["data"]["a2"] == "<class 'int'> = 123"

    # behavior is different to query parameter
    rv = http.post("/args", json={"a1": "123", "a1": "456"})
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'str'> = 456"

    # rv = http.get("/args?a4=123&a4=456")
    # assert rv.status_code == 200
    # # print(rv.json()["data"]["a4"])
    # assert rv.json()["data"]["a4"] == "<class 'list'> = [123, 456]"

    rv = http.post("/args", json={"a5": True})
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = http.post("/args", json={"a5": False})
    assert rv.status_code == 200
    assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = http.get("/args?a5=0")
    # assert rv.status_code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = http.get("/args?a5=on")
    # assert rv.status_code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = True"
    #
    # behavior is different to query parameter
    # rv = http.get("/args?a5=off")
    # assert rv.status_code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = False"

    # behavior is different to query parameter
    # rv = http.get("/args?a5=T")
    # assert rv.status_code == 200
    # assert rv.json()["data"]["a5"] == "<class 'bool'> = True"

    rv = http.post("/args", json={"a5": "xyz"})
    assert rv.status_code == 400
    assert 'parameter [a5] expected as_type [bool]' in rv.json()["error"]

    rv = http.post("/args", json={"a6": 123.456})
    assert rv.status_code == 200
    assert rv.json()["data"]["a6"] == "<class 'float'> = 123.456"

    rv = http.post("/args", json={"a7": {"b": "hello", "a": 123}})
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a7"] == "<class 'dict'> = {\"a\": 123, \"b\": \"hello\"}"

    rv = http.post("/args", json={"a8": '2018-2-01'})
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 00:00:00"

    rv = http.post("/args", json={"a8": '2018-2-01T12:34:55'})
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2018-02-01 12:34:55"

    rv = http.post("/args", json={"a8": '2009-01-01T12:55:12 CET'})
    assert rv.status_code == 200
    assert rv.json()["data"][
               "a8"] == "<class 'datetime.datetime'> = 2009-01-01 11:55:12"


def test_conv_error(http):
    rv = http.post("/args")
    assert rv.status_code == 200
    assert rv.json()["data"]["a1"] == "<class 'NoneType'> = None"
    # rv = http.get('/args?a8=9999-aa-bb')
    # assert rv.status_code == 400
    # assert "parameter [a8] expected as_type [datetime]" in rv.json()["error"]
    # import time
    # time.sleep(3)
    # print("OK")


if __name__ == '__main__':
    serve(CoreApiTestServer)
