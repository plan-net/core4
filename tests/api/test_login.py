import numpy as np
import pandas as pd
import time
import re
import pytest
import datetime
import core4.logger
import core4.util
import core4.util.node
import core4.util.tool
from core4.api.v1.application import CoreApiContainer, CoreApiServerTool
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role
import core4.service.setup
import core4.api.v1.util
import tornado.web
import tornado.httpclient
import os
import logging
import pymongo
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
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 1"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool False"
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


class SimpleHandler(CoreRequestHandler):
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
                "datetime": core4.util.node.now(),
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
        ("/simple", SimpleHandler)
    ]


class MyApp2(CoreApiContainer):
    root = "/app2"
    debug = True
    rules = [
        ("/simple", SimpleHandler)
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


async def test_login(http_server_client):
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/simple?val=456')
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    resp = await http_server_client.fetch(
        '/app1/login?username=admin&password=hans', method="POST", body="")
    assert resp.code == 200
    resp = await http_server_client.post(
        '/app1/login?username=admin&password=hans')
    assert resp.code == 200
    resp = await http_server_client.fetch(
        '/app1/login', method="POST",
        headers={"Content-Type": "application/json"},
        body='{"username": "admin", "password": "hans"}')
    assert resp.code == 200
    resp = await http_server_client.post(
        '/app1/login', body={"username": "admin", "password": "hans"})
    assert resp.code == 200

async def test_no_args(http_server_client):
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/login')
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/login?bla=1')
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/login?username=abc')
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/login?username=admin&password=1')

async def test_pass_auth(http_server_client):
    resp = await http_server_client.fetch('/app1/profile'
                                          '?username=admin&password=hans')
    assert resp.code == 200

async def test_login_success(http_server_client):
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch('/app1/login?token=' + token)
    assert resp.code == 200

async def test_token_header(http_server_client):
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]

    resp = await http_server_client.fetch('/app1/login?token=' + token)
    assert resp.code == 200


async def test_token_expired(http_server_client):
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    for i in range(5):
        await http_server_client.fetch('/app1/profile?token=' + token)
        assert resp.code == 200
        time.sleep(0.1)
    time.sleep(2)
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/profile?token=' + token)

async def test_token_extended(http_server_client):
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]

    async def run5(t):
        for i in range(5):
            resp = await http_server_client.fetch(
                '/app1/profile', method="GET",
                headers={"Authorization": "Bearer " + t})
            assert resp.code == 200
            time.sleep(0.05)

    await run5(token)
    # refresh token
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token2 = data["data"]["token"]

    await run5(token2)

    # data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    # token = data["data"]["token"]

    time.sleep(1.6)

    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/profile?token=' + token)
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/profile?token=' + token2)


async def test_restricted_user(http_server_client):
    Role(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=[]
    ).save()
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=user&password=password')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch(
            '/app1/profile', headers={"Authorization": "Bearer " + token})

async def test_granted_user(http_server_client):
    Role(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request.standard"]
    ).save()
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=user&password=password')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    resp = await http_server_client.fetch(
        '/app1/profile', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200

async def test_unmatched_permission(http_server_client):
    Role(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request.xxx"]
    ).save()
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=user&password=password')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch(
            '/app1/profile', headers={"Authorization": "Bearer " + token})

async def test_profile(http_server_client):
    Role(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request"]
    ).save()
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=user&password=password')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    resp = await http_server_client.fetch(
        '/app1/profile', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    from pprint import pprint
    pprint(core4.api.v1.util.json_decode(resp.body.decode("utf-8")))

async def test_profile_cascade(http_server_client):
    role1 = Role(
        name="role",
        realname="test role",
        perm=["api://core4.api.v1.abc"]
    )
    role2 = Role(
        name="role2",
        realname="test role",
        perm=["api://core4.api.v1.aaa"]
    )
    role2.save()
    role1.save()
    user = Role(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request"],
        role=[role1, role2]
    )
    user.save()
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=user&password=password')
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))
    token = data["data"]["token"]
    resp = await http_server_client.fetch(
        '/app1/login', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    resp = await http_server_client.fetch(
        '/app1/profile', headers={"Authorization": "Bearer " + token})
    assert resp.code == 200
    data = core4.api.v1.util.json_decode(resp.body.decode("utf-8"))["data"]
    assert data["_id"] == str(user._id)
    assert data["email"] == str(user.email)
    assert data["name"] == user.name
    assert data["realname"] == user.realname
    assert data["perm"] == ['api://core4.api.v1.aaa',
                            'api://core4.api.v1.abc',
                            'api://core4.api.v1.request']
    assert data["last_login"] is not None
    assert data["is_active"]
    assert data["role"] == ['role', 'role2', 'user']
    assert data["token_expires"] is not None

async def test_password_reset(http_server_client):
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=hans')
    assert resp.code == 200
    resp = await http_server_client.put('/app1/login?email=mail@mailer.com')
    assert resp.code == 200
    from core4.queue.worker import CoreWorker
    from core4.queue.main import CoreQueue
    q = core4.queue.main.CoreQueue()
    w = CoreWorker()
    w.startup()
    w.work_jobs()
    import time
    while True:
        waiting = sum([1 for job in q.get_queue_state() if job["state"] in ("running", "pending")])
        if waiting == 0:
            break
        time.sleep(0.25)
    data = list(q.config.sys.log.find())
    msg = [d for d in data if "send mail" in d["message"]][0]
    token = re.search(r"token = ([^\s+]+)", msg["message"]).groups()[0]
    w.shutdown()
    resp = await http_server_client.put('/app1/login?password=123456&token='
                                        + token)
    assert resp.code == 200
    resp = await http_server_client.fetch('/app1/login'
                                          '?username=admin&password=123456')
    assert resp.code == 200
    with pytest.raises(tornado.httpclient.HTTPClientError):
        await http_server_client.fetch('/app1/login'
                                       '?username=admin&password=hans')

# async def test_data_request(http_server_client):
#     resp = await http_server_client.fetch('/app1/data/request')
#     assert resp.code == 200

if __name__ == '__main__':
    from core4.api.v1.application import serve
    serve(MyApp2)

