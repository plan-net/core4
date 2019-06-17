import os
import re
import datetime
import pytest
import json

import core4.queue.main
from tests.api.test_test import setup, core4api
from core4.api.v1.tool.functool import serve
from core4.api.v1.server import CoreApiServer


_ = setup
_ = core4api


@pytest.fixture()
def short_expire(tmpdir):
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 8"
    os.environ["CORE4_OPTION_api__token__refresh"] = "!!int 4"


async def test_login(core4api):
    resp = await core4api.get(
        '/core4/api/v1/login?username=admin&password=hans')
    assert resp.code == 200
    js = resp.json()
    assert "timestamp" in js
    assert "_id" in js
    assert js["code"] == 200
    assert js["message"] == "OK"
    assert resp.headers.get("token") == resp.json()["data"]["token"]
    assert resp.json()["data"]["token"] is not None


async def test_cookie(core4api):
    resp = await core4api.get(
        '/core4/api/v1/login?username=admin&password=hans')
    assert resp.code == 200
    cookie = resp.headers.get("set-cookie")
    resp = await core4api.get(
        '/core4/api/v1/login', headers={"Cookie": cookie})
    assert resp.code == 200


async def test_token(core4api):
    resp = await core4api.get(
        '/core4/api/v1/login?username=admin&password=hans')
    assert resp.code == 200
    token = resp.json()["data"]["token"]
    resp = await core4api.get('/core4/api/v1/login?token=' + token)
    assert resp.code == 200


async def test_body(core4api):
    resp = await core4api.post(
        '/core4/api/v1/login', body={"username": "admin", "password": "hans"})
    assert resp.code == 200
    token = resp.json()["data"]["token"]
    resp = await core4api.post('/core4/api/v1/login', body={"token": token})
    assert resp.code == 200


async def test_invalid_login(core4api):
    resp = await core4api.post(
        '/core4/api/v1/login', body={"username": "admin", "password": "xxxx"})
    assert resp.code == 401

    resp = await core4api.post(
        '/core4/api/v1/login', json={"username": "admin", "password": "xxxx"})
    assert resp.code == 401

    resp = await core4api.post(
        '/core4/api/v1/login', json={"username": "admin", "password": "hans"})
    assert resp.code == 200


async def test_no_args(core4api):
    rv = await core4api.get("/core4/api/v1/login")
    assert rv.code == 401
    rv = await core4api.get("/core4/api/v1/login?bla=1")
    assert rv.code == 401
    rv = await core4api.get('/core4/api/v1/login?username=abc')
    assert rv.code == 401
    rv = await core4api.get('/core4/api/v1/login?username=admin&password=1')
    assert rv.code == 401


async def test_pass_auth(core4api):
    rv = await core4api.get('/core4/api/v1/profile')
    assert rv.code == 401
    rv = await core4api.get(
        '/core4/api/v1/profile?username=admin&password=hans')
    assert rv.code == 200


async def test_login_expired(short_expire, core4api):
    await core4api.login()
    rv = await core4api.get('/core4/api/v1/profile')
    assert rv.code == 200
    t0 = datetime.datetime.now()
    while True:
        rv = await core4api.get('/core4/api/v1/profile')
        if rv.code != 200:
            break
    assert round((datetime.datetime.now() - t0).total_seconds(), 0) >= 8
    assert rv.code == 401


async def test_login_extended(short_expire, core4api):
    await core4api.login()
    rv = await core4api.get('/core4/api/v1/profile')
    assert rv.code == 200
    t0 = datetime.datetime.now()
    while True:
        rv = await core4api.get('/core4/api/v1/profile')
        print("check")
        if "token" in rv.headers:
            core4api.token = rv.headers["token"]
            break
    assert rv.code == 200
    assert round((datetime.datetime.now() - t0).total_seconds()) >= 4
    t0 = datetime.datetime.now()
    while True:
        rv = await core4api.get('/core4/api/v1/profile')
        if rv.code != 200:
            break
    assert round((datetime.datetime.now() - t0).total_seconds()) >= 8
    assert rv.code == 401

async def test_restricted_user(core4api):
    await core4api.login()
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="user",
        realname="test user",
        passwd="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/roles/" + user_id)
    assert rv.code == 200
    assert rv.json()["data"]["name"] == "user"

    js = json.dumps({"name": "user"})
    rv = await core4api.get("/core4/api/v1/roles?filter=" + js)
    assert rv.code == 200
    assert rv.json()["total_count"] == 1

    await core4api.login("user", "password")
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.json()["data"]["name"] == "user"
    assert rv.code == 200

    core4api.set_admin()
    rv = await core4api.put("/core4/api/v1/roles/" + user_id, json=dict(
        perm=[],
        etag=etag
    ))
    assert rv.code == 200

    await core4api.login("user", "password")
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 403


async def test_login_inactive(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="user",
        realname="test user",
        passwd="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    assert rv.code == 200
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    await core4api.login("user", "password")

    core4api.set_admin()
    rv = await core4api.put("/core4/api/v1/roles/" + user_id, json=dict(
        is_active=False,
        etag=etag
    ))
    assert rv.code == 200

    core4api.token = None
    rv = await core4api.get("/core4/api/v1/login?username=user&password=password")
    assert rv.code == 401


def test_admin_settings1():
    os.environ["CORE4_OPTION_api__admin_username"] = "hello"
    os.environ["CORE4_OPTION_api__admin_password"] = "~"
    os.environ["CORE4_OPTION_api__contact"] = "mail@test.com"
    with pytest.raises(TypeError):
        serve(CoreApiServer)


def test_admin_settings2():
    os.environ["CORE4_OPTION_api__admin_username"] = "~"
    os.environ["CORE4_OPTION_api__admin_password"] = "123456"
    os.environ["CORE4_OPTION_api__contact"] = "mail@test.com"
    with pytest.raises(TypeError):
        serve(CoreApiServer)


def test_admin_settings3():
    os.environ["CORE4_OPTION_api__admin_username"] = "hello"
    os.environ["CORE4_OPTION_api__admin_password"] = "123456"
    os.environ["CORE4_OPTION_api__contact"] = "~"
    with pytest.raises(TypeError):
        serve(CoreApiServer)


async def test_password_reset(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="user",
        realname="test user",
        passwd="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))
    user_id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    assert rv.code == 200

    await core4api.login("user", "password")
    rv = await core4api.put("/core4/api/v1/login?email=test@user.com")
    assert rv.code == 200

    q = core4.queue.main.CoreQueue()
    data = list(q.config.sys.log.find())
    msg = [d for d in data if "send token" in d["message"]][0]
    token = re.search(r"token \[(.+?)\]", msg["message"]).groups()[0]
    rv = await core4api.put("/core4/api/v1/login?token=" + token + "&password=world")
    assert rv.code == 200

    core4api.token = None
    rv = await core4api.get("/core4/api/v1/login?username=user&password=password")
    assert rv.code == 401

    rv = await core4api.get("/core4/api/v1/login?username=user&password=world")
    assert rv.code == 200
