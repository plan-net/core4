import logging
import multiprocessing
import os

import pymongo
import pytest
import requests
import time

import core4.error
import core4.logger.mixin
import core4.service
from core4.api.v1.tool import serve_all

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


@pytest.fixture()
def token():
    server = multiprocessing.Process(target=serve_all,
                                     kwargs={"filter": "project.api",
                                             "port": 5555})
    server.start()
    while True:
        try:
            requests.get("http://localhost:5555/project/profile", timeout=1)
            break
        except:
            pass
        time.sleep(1)
    signin = requests.get(
        "http://localhost:5555/project/login?username=admin&password=hans")
    token = signin.json()["data"]["token"]
    yield token
    requests.get("http://localhost:5555/project/kill")
    server.join()


def test_simple(token):
    rv = requests.get("http://localhost:5555/project/req1?token=" + token)
    assert rv.status_code == 200
    rv = requests.get("http://localhost:5555/project/req2?token=" + token)
    assert rv.status_code == 200
    rv = requests.get("http://localhost:5555/project/stat1/")
    assert rv.status_code == 200
    assert b"variable hello from ProjectServer1" in rv.content
    assert b'href="/project/stat1/index.html"' in rv.content
    assert b'href="/another/stat2/index.html"' in rv.content
    rv = requests.get("http://localhost:5555/another/req1?token=" + token)
    assert rv.status_code == 200
    rv = requests.get("http://localhost:5555/another/req2?token=" + token)
    assert rv.status_code == 404
    signin = requests.get(
        "http://localhost:5555/project/login?username=admin&password=hans")
    rv = requests.get("http://localhost:5555/another/stat2/default.html",
                      cookies=signin.cookies)
    rv = requests.get("http://localhost:5555/another/stat2/",
                      cookies=signin.cookies)
    assert rv.status_code == 200
    assert b"<title>my Test2</title>" in rv.content


def test_duplicate():
    with pytest.raises(core4.error.Core4SetupError):
        serve_all("project")


def test_unknown_project(token):
    rv = requests.get("http://localhost:5555/xxx")
    assert rv.status_code == 404
    rv = requests.get("http://localhost:5555/project")
    assert rv.status_code == 404
    rv = requests.get("http://localhost:5555/project/req1")
    assert rv.status_code == 401


def test_asset(token):
    rv = requests.get("http://localhost:5555/project/req1?token=" + token)
    assert rv.status_code == 200
    rv = requests.get("http://localhost:5555/another/stat2/default.html")
    assert rv.status_code == 401
    rv = requests.get(
        "http://localhost:5555/another/stat2/default.html?token=" + token)
    assert rv.status_code == 200


def test_cookie(token):
    signin = requests.get(
        "http://localhost:5555/project/login?username=admin&password=hans")
    rv = requests.get("http://localhost:5555/another/stat2/default.html",
                      cookies=signin.cookies)
    assert rv.status_code == 200


def test_304(token):
    rv = requests.get("http://localhost:5555/project/stat1/asset/head.png")
    assert rv.status_code == 200
    headers = {
        "If-Modified-Since": rv.headers["Last-Modified"]
    }
    rv = requests.get("http://localhost:5555/project/stat1/asset/head.png",
                      headers=headers)
    assert rv.status_code == 304
    assert rv.content == b''


def test_favicon(token):
    rv = requests.get("http://localhost:5555/favicon.ico")
    assert rv.status_code == 200


