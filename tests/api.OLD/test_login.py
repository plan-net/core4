import logging
import os
import re

import datetime
import pymongo
import pytest

import core4.logger.mixin
import core4.service
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.tool.functool import serve
from core4.queue.main import CoreQueue
from tests.api.test_response import LocalTestServer, StopHandler

MONGO_URL = 'mongodb://core:654321@localhost:27017'
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
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 8"
    os.environ["CORE4_OPTION_api__token__refresh"] = "!!int 4"
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


class CoreApiTestServer(CoreApiContainer):
    enabled = False
    rules = [
        (r'/kill', StopHandler),
        (r'/roles/?(.*)', RoleHandler),
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
    rv = http.get("/core4/api/profile", base=False)
    assert rv.status_code == 200


def test_login(http):
    rv = http.get("/core4/api/login?username=admin&password=hans",
                  base=False)
    assert rv.status_code == 200
    rv = http.post("/core4/api/login?username=admin&password=hans",
                   base=False)
    assert rv.status_code == 200
    rv = http.post("/core4/api/login", base=False,
                   json={"username": "admin", "password": "hans"})
    assert rv.status_code == 200


def test_invalid_login(http):
    token = http.token
    http.token = None
    rv = http.post("/core4/api/login", base=False,
                   json={"username": "admin", "password": "xxx"})
    assert rv.status_code == 401
    http.token = token


def test_no_args(http):
    token = http.token
    http.token = None
    rv = http.get("/core4/api/login", base=False)
    assert rv.status_code == 401
    rv = http.get("/core4/api/login?bla=1", base=False)
    assert rv.status_code == 401
    rv = http.get('/core4/api/login?username=abc', base=False)
    assert rv.status_code == 401
    rv = http.get('/core4/api/login?username=admin&password=1', base=False)
    assert rv.status_code == 401
    http.token = token


def test_pass_auth(http):
    token = http.token
    http.token = None
    rv = http.get('/core4/api/profile', base=False)
    assert rv.status_code == 401
    rv = http.get('/core4/api/profile?username=admin&password=hans',
                  base=False)
    assert rv.status_code == 200
    http.token = token


def test_login_success(http):
    token = http.token
    http.token = None
    rv = http.get('/core4/api/profile?token=' + token, base=False)
    assert rv.status_code == 200
    http.token = token


def test_login_expired(http):
    rv = http.get('/core4/api/profile', base=False)
    assert rv.status_code == 200
    t0 = datetime.datetime.now()
    while True:
        rv = http.get('/core4/api/profile', base=False)
        if rv.status_code != 200:
            break
    assert round((datetime.datetime.now() - t0).total_seconds(), 0) >= 8
    assert rv.status_code == 401


def test_login_extended(http):
    rv = http.get('/core4/api/profile', base=False)
    assert rv.status_code == 200
    t0 = datetime.datetime.now()
    while True:
        rv = http.get('/core4/api/profile', base=False)
        if "token" in rv.headers:
            http.token = rv.headers["token"]
            break
    assert rv.status_code == 200
    assert round((datetime.datetime.now() - t0).total_seconds()) >= 4
    t0 = datetime.datetime.now()
    while True:
        rv = http.get('/core4/api/profile', base=False)
        if rv.status_code != 200:
            break
    assert round((datetime.datetime.now() - t0).total_seconds()) >= 8
    assert rv.status_code == 401


def test_roles(http):
    rv = http.get("/roles")
    assert len(rv.json()["data"]) == 2


def test_profile_cascade(http):
    rv = http.post("/roles", json=dict(
        name="role",
        realname="test role",
        perm=["api://core4.api.v1.abc"]
    ))
    assert rv.status_code == 200
    rv = http.post("/roles", json=dict(
        name="role2",
        realname="test role2",
        perm=["api://core4.api.v1.aaa"]
    ))
    assert rv.status_code == 200
    rv = http.post("/roles", json=dict(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request"],
        role=["role", "role2"]
    ))
    assert rv.status_code == 200
    user_id = rv.json()["data"]["_id"]
    http.token = None
    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 200
    token = rv.json()["data"]["token"]
    http.token = token
    rv = http.get("/core4/api/profile", base=False)
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["name"] == "user"
    assert data["_id"] == user_id
    assert data["email"] == "test@user.com"
    assert data["realname"] == "test user"
    assert data["perm"] == ['api://core4.api.v1.aaa',
                            'api://core4.api.v1.abc',
                            'api://core4.api.v1.request']
    assert data["last_login"] is not None
    assert data["is_active"]
    assert data["role"] == ['role', 'role2']
    assert data["token_expires"] is not None


def test_restricted_user(http):
    rv = http.get("/roles")
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 2
    rv = http.post("/roles", json=dict(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    assert rv.status_code == 200
    rv = http.get("/roles")
    assert len(rv.json()["data"]) == 3
    admin_token = http.token
    http.token = None
    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 200
    token = rv.json()["data"]["token"]
    http.token = token
    rv = http.get("/core4/api/profile", base=False)
    assert rv.json()["data"]["name"] == "user"
    assert rv.status_code == 200

    http.token = admin_token
    rv = http.put("/roles/" + user_id, json=dict(
        perm=[],
        etag=etag
    ))
    assert rv.status_code == 200

    http.token = token
    rv = http.get("/core4/api/profile", base=False)
    assert rv.status_code == 403


def test_password_reset(http):
    rv = http.post("/roles", json=dict(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    assert rv.status_code == 200

    admin_token = http.token
    http.token = None

    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 200

    rv = http.put("/core4/api/login?email=test@user.com", base=False)
    assert rv.status_code == 200

    q = core4.queue.main.CoreQueue()
    data = list(q.config.sys.log.find())
    msg = [d for d in data if "send token" in d["message"]][0]
    token = re.search(r"token \[(.+?)\]", msg["message"]).groups()[0]
    rv = http.put("/core4/api/login?token=" + token + "&password=world",
                  base=False)
    assert rv.status_code == 200

    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 401

    rv = http.get("/core4/api/login?username=user&password=world",
                  base=False)
    assert rv.status_code == 200


def test_login_inactive(http):
    rv = http.post("/roles", json=dict(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    assert rv.status_code == 200

    admin_token = http.token
    http.token = None

    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 200

    http.token = admin_token
    rv = http.put("/roles/" + user_id, json=dict(
        is_active=False,
        etag=etag
    ))
    assert rv.status_code == 200

    http.token = None

    rv = http.get("/core4/api/login?username=user&password=password",
                  base=False)
    assert rv.status_code == 401


class CoreApiTestServer1(CoreApiContainer):
    rules = [
        (r'/kill', StopHandler)
    ]


def test_admin_settings1():
    os.environ["CORE4_OPTION_api__admin_username"] = "hello"
    os.environ["CORE4_OPTION_api__admin_password"] = "~"
    os.environ["CORE4_OPTION_api__contact"] = "mail@test.com"
    with pytest.raises(TypeError):
        serve(CoreApiTestServer1)


def test_admin_settings2():
    os.environ["CORE4_OPTION_api__admin_username"] = "~"
    os.environ["CORE4_OPTION_api__admin_password"] = "123456"
    os.environ["CORE4_OPTION_api__contact"] = "mail@test.com"
    with pytest.raises(TypeError):
        serve(CoreApiTestServer1)


def test_admin_settings3():
    os.environ["CORE4_OPTION_api__admin_username"] = "hello"
    os.environ["CORE4_OPTION_api__admin_password"] = "123456"
    os.environ["CORE4_OPTION_api__contact"] = "~"
    with pytest.raises(TypeError):
        serve(CoreApiTestServer1)
