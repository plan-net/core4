import logging
import os
import re

import datetime
import pymongo
import pytest

import core4.logger.mixin
import core4.service
from core4.api.v1.application import CoreApiContainer
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


def test_get_default_setting(http):
    response = http.get("/core4/api/v1/login?username=admin&password=hans", base=False)
    assert response.ok

    response = http.get("/core4/api/v1/setting", base=False)
    assert response.json()["code"] == 200
    assert type(response.json()["data"]["_general"]) is dict

def test_set_system_setting(http):
    pass
    # data = {"data": 123}
    # response = http.post("/core4/api/v1/setting/_project", json=data)
    # assert response.json()["code"] == 400
    #
    # data = {"data": 123}
    # response = http.post("/core4/api/v1/setting/_general", json=data)
    # assert response.json()["code"] == 400
    #
    # data = {"data": {"_general": 123}}
    # response = http.post("/core4/api/v1/setting", json=data)
    # assert response.json()["code"] == 400
    #
    # data = {"data": {"_other": 123}}
    # response = http.post("/core4/api/v1/setting", json=data)
    # assert response.json()["code"] == 400
    #
    # data = {"data": {"language": "UA"}}
    # response = http.post("/core4/api/v1/setting/_general", json=data)
    # assert response.json()["code"] == 200
    #
    # data = {"data": {"_general": {"language": "UA"}}}
    # response = http.post("/core4/api/v1/setting", json=data)
    # assert response.json()["code"] == 200

def test_override_default_settings():
    pass

def test_update_settings():
    pass

def test_create_nested_settings():
    pass

def test_update_nested_settings():
    pass

def test_get_nested_settings():
    pass

def test_get_settings_for_other_user():
    pass

def test_url_restriction(http):
    pass

def test_level1_structure(http):
    pass

def test_level2_structure(http):
    pass
