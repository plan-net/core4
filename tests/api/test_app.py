import numpy as np
import pandas as pd
import pytest
import datetime
import core4.logger
import core4.util
from core4.api.v1.application import CoreApiContainer, CoreApiServerTool
from core4.api.v1.request.main import CoreRequestHandler


class MainHandler(CoreRequestHandler):
    def get(self):
        val = self.get_argument("val", default=123)
        self.write("Hello, world: %s" % (val))
        self.logger.info("done doing")


class AnotherHandler(CoreRequestHandler):
    def get(self):
        val = self.get_argument("val", default=123)
        self.write("Hello, universe: %s" % (val))
        self.logger.info("done doing")


class DataRequest(CoreRequestHandler):
    async def get(self, path=None):
        if path == "/html":
            self.render("template1.html", var="world")
        elif path == "/df":
            result = self.blocking_method()
            n = 0
            for line in result.to_csv().split("\n"):
                n += 1
                self.write(line)
                if n % 100 == 0:
                    self.flush()
        else:
            self.write({
                "value": 123,
                "string": "abc",
                "datetime": core4.util.now(),
                "pathname": path
            })

    def blocking_method(self):
        n = 2400
        df = pd.DataFrame({'A': ['spam', 'eggs', 'spam', 'eggs'] * (n // 4),
                           'B': ['alpha', 'beta', 'gamma'] * (n // 3),
                           'C': [np.random.choice(pd.date_range(
                               datetime.datetime(2013, 1, 1),
                               datetime.datetime(2013, 1, 3))) for i in
                               range(n)],
                           'D': np.random.randn(n),
                           'E': np.random.randint(0, 4, n)})
        return df



class MyApp1(CoreApiContainer):
    root = "/app1"
    rules = [
        ("/test1", MainHandler),
        ("/test2", MainHandler),
        ("/data/request", DataRequest),
    ]


class MyApp2(CoreApiContainer):
    root = "/app2"
    debug = True
    rules = [
        ("/test1", AnotherHandler),
        ("/test2", MainHandler),
        ("/data(\/.+)?$", DataRequest),
    ]


@pytest.fixture
def app():
    return CoreApiServerTool().make_routes(MyApp1, MyApp2)


@pytest.fixture(autouse=True)
def reset():
    core4.logger.mixin.logon()


def test_package(app):
    assert app.rules[0].matcher.regex.pattern == "/app1.*$"
    assert app.rules[1].matcher.regex.pattern == "/app2.*$"


async def test_http_server_client(http_server_client):
    resp = await http_server_client.fetch('/app1/test1?val=456')
    assert b'Hello, world: 456' == resp.body
    assert resp.code == 200
    resp = await http_server_client.fetch('/app1/test1')
    assert b'Hello, world: 123' == resp.body
    assert resp.code == 200


async def test_apps(http_server_client):
    resp = await http_server_client.fetch('/app1/test1')
    assert b'Hello, world: 123' == resp.body
    assert resp.code == 200
    resp = await http_server_client.fetch('/app2/test1')
    assert b'Hello, universe: 123' == resp.body
    assert resp.code == 200


async def test_json(http_server_client):
    resp = await http_server_client.fetch('/app2/data')
    assert resp.code == 200
    print(str(resp.body.decode("utf-8")))
    resp = await http_server_client.fetch('/app2/data/html')
    assert resp.code == 200
    print(str(resp.body.decode("utf-8")))
    resp = await http_server_client.fetch('/app2/data/df')
    assert resp.code == 200
    print(str(resp.body.decode("utf-8")))

# async def test_data_request(http_server_client):
#     resp = await http_server_client.fetch('/app1/data/request')
#     assert resp.code == 200

if __name__ == '__main__':
    from core4.api.v1.application import serve
    serve(MyApp2)