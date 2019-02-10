import os
import random
import logging

import pymongo
import pytest

import core4.service
import core4.logger.mixin
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.setting import SettingHandler
from tests.api.test_response import LocalTestServer, StopHandler

MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


@pytest.fixture(autouse=True)
def setup(tmpdir):
    logging.shutdown()
    core4.logger.mixin.CoreLoggerMixin.completed = False

    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 8"
    os.environ["CORE4_OPTION_api__token__refresh"] = "!!int 4"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool True"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    os.environ["CORE4_OPTION_user_setting___general__language"] = "FR"

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
        (r'/setting/?(.*)', SettingHandler),
    ]


class HttpServer(LocalTestServer):
    def start(self, *args, **kwargs):
        return CoreApiTestServer


@pytest.fixture()
def http():
    server = HttpServer()
    yield server
    server.stop()


def test_general_url_restriction(http):
    data = {"data": {"_general": {"language": "UA"}}}
    response = http.post("/core4/api/v1/setting", json=data, base=False)
    assert response.ok
    assert response.json()["data"]["_general"]["language"] == "UA"

    response = http.get("/core4/api/v1/setting/_general//language", base=False)
    assert response.status_code == 400


def test_response_contains_data(http):
    to_send = {"_general": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok
    assert response.json()["data"] == to_send


def test_levels_restrictions(http):
    # empty key in level1
    to_send = {"": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.status_code == 400

    # empty key in level2
    to_send = {"_general": {"": {"code": "UA"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.status_code == 400

    # empty key in level2
    to_send = {"": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting/_general", json={"data": to_send}, base=False)
    assert response.status_code == 400

    # invalid level1 structure
    response = http.post("/core4/api/v1/setting", json={"data": 123}, base=False)
    assert response.status_code == 400

    # invalid level2 structure
    response = http.post("/core4/api/v1/setting/_general", json={"data": 123}, base=False)
    assert response.status_code == 400

    # invalid system key on level1, names with underscore reserved
    to_send = {"_project": {"language": {"code": "UA"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.status_code == 400

    # invalid system key on level1, names with underscore reserved
    to_send = {"language": {"code": "UA"}}
    response = http.post("/core4/api/v1/setting/_project", json={"data": to_send}, base=False)
    assert response.status_code == 400

    # empty resource in url
    to_send = {"code": "UA"}
    response = http.post("/core4/api/v1/setting//language", json={"data": to_send}, base=False)
    assert response.status_code == 400


def test_get_default_setting(http):
    response = http.get("/core4/api/v1/setting", base=False)
    assert response.ok

    general_ = response.json()["data"]["_general"]
    assert type(general_) is dict
    assert general_["language"] == "FR"


def test_default_settings_override(http):
    to_send = {"_general": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.json()["data"] == to_send


def test_delete_settings(http):
    to_send = {"_general": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.json()["data"] == to_send

    response = http.delete("/core4/api/v1/setting", base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.ok
    assert response.json()["data"]["_general"]["language"] == "FR"


def test_delete_nested_settings(http):
    to_send = {"project": {"setting1": 57, "setting2": 111}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.json()["data"] == {"_general": {"language": "FR"}, "project": {"setting1": 57, "setting2": 111}}

    response = http.delete("/core4/api/v1/setting/project/setting1", base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.ok
    assert response.json()["data"] == {"_general": {"language": "FR"}, "project": {"setting2": 111}}

    response = http.delete("/core4/api/v1/setting/project", base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.ok
    assert response.json()["data"] == {"_general": {"language": "FR"}}


def test_user_override(http):
    response = http.post("/roles", json=dict(
        name="test",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))

    assert response.ok
    test_data = {"random": random.randint(0, 42)}
    response = http.post("/core4/api/v1/setting/test_project/test_setting?username=test", json={"data": test_data}, base=False)
    assert response.ok

    original_token = http.token
    http.token = None
    response = http.get('/core4/api/v1/login?username=test&password=password', base=False)
    assert response.ok
    http.token = response.json()["data"]["token"]

    response = http.get("/core4/api/v1/setting/test_project/test_setting", base=False)
    assert response.ok
    assert response.json()["data"] == test_data
    http.token = original_token


def test_set_system_setting(http):
    data = {"data": 123}
    response = http.post("/core4/api/v1/setting/_project", json=data, base=False)
    assert response.json()["code"] == 400

    data = {"data": 123}
    response = http.post("/core4/api/v1/setting/_general", json=data, base=False)
    assert response.json()["code"] == 400

    data = {"data": {"_general": 123}}
    response = http.post("/core4/api/v1/setting", json=data, base=False)
    assert response.json()["code"] == 400

    data = {"data": {"_other": 123}}
    response = http.post("/core4/api/v1/setting", json=data, base=False)
    assert response.json()["code"] == 400

    data = {"data": {"_general": {"language": "UA"}}}
    response = http.post("/core4/api/v1/setting", json=data, base=False)
    assert response.json()["code"] == 200
    assert response.json()["data"]["_general"]["language"] == "UA"

    data = {"data": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting/_general", json=data, base=False)
    assert response.status_code == 200


def test_update_settings(http):
    to_send = {"_general": {"language": "UA"}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.put("/core4/api/v1/setting/_general/language", json={"data": "RU"}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.ok
    assert response.json()["data"]["_general"]["language"] == "RU"


def test_create_nested_settings(http):
    to_send = {"_general": {"language": {"code": "UA"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.post("/core4/api/v1/setting/_general/language", json={"data": {"name": "Ukraine"}}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting/_general", base=False)
    assert response.ok
    assert response.json()["data"]["language"] == {"code": "UA", "name": "Ukraine"}


def test_empty_string_as_key(http):
    to_send = {"_general": {"language": {"code": "UA"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    # after level2 no restrictions, bullshit in, bullshit out :[
    response = http.post("/core4/api/v1/setting/_general/language", json={"data": {"": "Ukraine"}}, base=False)
    assert response.status_code == 200

    response = http.get("/core4/api/v1/setting/_general", base=False)
    assert response.ok
    assert response.json()["data"]["language"] == {"code": "UA", "": "Ukraine"}


def test_get_nested_settings(http):
    to_send = {"_general": {"language": {"code": "LT"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting/_general/language/code", base=False)
    assert response.ok
    assert response.json()["data"] == "LT"


def test_update_nested_settings(http):
    to_send = {"_general": {"language": {"code": "LT"}}}
    response = http.post("/core4/api/v1/setting", json={"data": to_send}, base=False)
    assert response.ok

    response = http.post("/core4/api/v1/setting/_general/language", json={"data": {"name": "Ukraine"}}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting/_general/language", base=False)
    assert response.ok
    assert response.json()["data"] == {"code": "LT", "name": "Ukraine"}

    response = http.put("/core4/api/v1/setting/_general/language/code", json={"data": "RU"}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting/_general/language", base=False)
    assert response.ok
    assert response.json()["data"] == {"code": "RU", "name": "Ukraine"}

    response = http.put("/core4/api/v1/setting/_general/language/name", json={"data": "Russia"}, base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting/_general/language", base=False)
    assert response.ok
    assert response.json()["data"] == {"code": "RU", "name": "Russia"}


