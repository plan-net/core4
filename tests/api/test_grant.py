import pymongo
import pytest

import core4.api.v1.request.role.field
from tests.api.test_test import setup, mongodb, core4api

_ = setup
_ = mongodb
_ = core4api


async def test_login(core4api):
    await core4api.login()
    resp = await core4api.get(
        '/core4/api/v1/profile')
    assert resp.code == 200


async def test_grant(core4api):
    await core4api.login()
    data = {
        "name": "test_role1",
        "realname": "test role1",
        "password": "123456",
        "email": "test@mail.com",
        "role": [
            "standard_user"
        ],
        "perm": []
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    admin_token = core4api.token
    core4api.token = None
    rv = await core4api.get(
        "/core4/api/v1/login?username=test_role1&password=123456")
    assert rv.code == 200
    token = rv.json()["data"]["token"]
    core4api.token = token

    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200

    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200

    access = rv.json()["data"]["mongodb"]
    print(access)
    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test"
        ]
    }

    core4api.token = admin_token
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    # print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    core4api.token = token
    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200
    access = rv.json()["data"]["mongodb"]
    print(access)

    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    print(mongo["core4test"].list_collection_names())

    data = {
        "etag": etag,
        "realname": "no change"
    }

    core4api.token = admin_token
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    # print(mongo.server_info())
    print(mongo["core4test"].list_collection_names())

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test",
            "mongodb://other"
        ]
    }

    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200

    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    with pytest.raises(pymongo.errors.OperationFailure):
        print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    core4api.token = token
    rv = await core4api.post("/core4/api/v1/access/mongodb")
    assert rv.code == 200
    print(rv.json())
    access = rv.json()["data"]
    print(access)

    mongo = pymongo.MongoClient(
        "mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    _ = mongo["core4test"].list_collection_names()


async def add_user(http, username):
    http.set_admin()
    rv = await http.post("/core4/api/v1/roles",
                         body={
                             "name": username,
                             "role": ["standard_user"],
                             "email": username + "@mail.com",
                             "password": username
                         })
    assert rv.code == 200
    http.token = None
    conn = await http.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    http.token = conn.json()["data"]["token"]


async def test_server_test(core4api):
    await core4api.login()
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
    await add_user(core4api, "user1")
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 403
    rv = await core4api.get("/core4/api/v1/jobs/enqueue")
    assert rv.code == 403
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.code == 403
    rv = await core4api.get("/core4/api/v1/logout")
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/_info")
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/xxx")
    assert rv.code == 404
    rv = await core4api.post("/core4/api/v1/jobs")
    assert rv.code == 403

    rv = await core4api.post("/core4/api/v1/system")
    assert rv.code == 403

    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/event/history")
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/setting")
    assert rv.code == 200


async def add_job_user(http, username, perm):
    http.set_admin()
    rv = await http.post("/core4/api/v1/roles",
                         body={
                             "name": username,
                             "role": ["standard_user"],
                             "email": username + "@mail.com",
                             "password": username,
                             "perm": perm
                         })
    assert rv.code == 200
    http.token = None
    conn = await http.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    http.token = conn.json()["data"]["token"]
    return http.token


async def test_enqeuue(core4api):
    await core4api.login()
    await add_job_user(
        core4api, "user1", [
            "api://core4.api.v1.request.queue.job.JobPost",
            "api://core4.api.v1.request.queue.job.JobHandler",
            "job://core4.queue.helper.*/x"
        ])
    rv = await core4api.post(
        "/core4/api/v1/jobs/enqueue?name=core4.queue.helper.job.example.DummyJob")
    assert rv.code == 200
    jid = rv.json()["data"]["_id"]
    rv = await core4api.get("/core4/api/v1/jobs/" + jid)
    assert rv.code == 200
    await add_job_user(
        core4api, "user2",
        ["api://core4.api.v1.request.queue.job.JobHandler"])
    rv = await core4api.post(
        "/core4/api/v1/jobs/enqueue?name=core4.queue.helper.job.example.DummyJob")
    assert rv.code == 403
    rv = await core4api.get("/core4/api/v1/jobs/" + jid)
    assert rv.code == 403
    await add_job_user(
        core4api, "user3", [
            "api://core4.api.v1.request.queue.job.JobHandler",
            "job://core4.queue.helper.*/r"
        ])
    rv = await core4api.post(
        "/core4/api/v1/jobs/enqueue?name=core4.queue.helper.job.example.DummyJob")
    assert rv.code == 403
    rv = await core4api.get("/core4/api/v1/jobs/" + jid)
    assert rv.code == 200


class MyJob(core4.queue.job.CoreJob):
    author = "mra"


async def test_job_listing(core4api):
    await core4api.login()
    for i in range(0, 10):
        rv = await core4api.post("/core4/api/v1/jobs/enqueue", body={
            "name": "core4.queue.helper.job.example.DummyJob",
            "id": i + 1
        }, headers={"Content-Type": "application/json"})
        assert rv.code == 200

    for i in range(0, 6):
        rv = await core4api.post("/core4/api/v1/jobs/enqueue", body={
            "name": "tests.api.test_grant.MyJob",
            "id": i + 1
        }, headers={"Content-Type": "application/json"})
        assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 16

    await add_job_user(core4api, "user1", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://core4.queue.helper.job.*/r"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 10

    core4api.set_admin()
    await add_job_user(core4api, "user2", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://core4.queue.helper.*/x"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 10

    core4api.set_admin()
    await add_job_user(core4api, "user3", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://tests.+/r"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 6

    rv = await core4api.post("/core4/api/v1/jobs/enqueue", body={
        "name": "tests.api.test_grant.MyJob"
    }, headers={"Content-Type": "application/json"})
    assert rv.code == 403

    core4api.set_admin()
    await add_job_user(core4api, "user4", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://tests.+/x"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 6

    rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
        "name": "tests.api.test_grant.MyJob"
    })
    assert rv.code == 200
    job_id = rv.json()["data"]["_id"]

    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 7

    rv = await core4api.get("/core4/api/v1/jobs/" + job_id)
    assert rv.code == 200


async def test_job_access(core4api):
    await core4api.login()
    token3 = await add_job_user(core4api, "user3", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://tests.+/r"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.code == 200
    assert rv.json()["total_count"] == 0

    rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
        "name": "tests.api.test_grant.MyJob"
    })
    assert rv.code == 403

    token4 = await add_job_user(core4api, "user4", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://tests.+/x"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 0

    rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
        "name": "tests.api.test_grant.MyJob"
    })
    assert rv.code == 200
    job_id = rv.json()["data"]["_id"]

    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 1

    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 1

    rv = await core4api.get("/core4/api/v1/jobs/" + job_id)
    assert rv.code == 200

    core4api.token = token3
    rv = await core4api.get("/core4/api/v1/jobs/" + job_id)
    assert rv.code == 200

    rv = await core4api.delete("/core4/api/v1/jobs/" + job_id)
    assert rv.code == 403

    rv = await core4api.put("/core4/api/v1/jobs/" + job_id + "?action=kill")
    assert rv.code == 403

    core4api.token = token4
    rv = await core4api.put("/core4/api/v1/jobs/" + job_id + "?action=kill")
    assert rv.code == 200

    core4api.token = token3
    rv = await core4api.put(
        "/core4/api/v1/jobs/" + job_id + "?action=restart")
    assert rv.code == 403

    core4api.token = token4
    rv = await core4api.put(
        "/core4/api/v1/jobs/" + job_id + "?action=restart")
    assert rv.code == 400

    rv = await core4api.delete("/core4/api/v1/jobs/" + job_id)
    assert rv.code == 200


async def test_profile_cascade(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="role",
        realname="test role",
        perm=["api://core4.api.v1.abc"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="role2",
        realname="test role2",
        perm=["api://core4.api.v1.aaa"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="user",
        realname="test user",
        password="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request"],
        role=["role", "role2"]
    ))
    assert rv.code == 200
    user_id = rv.json()["data"]["_id"]
    core4api.token = None
    await core4api.login("user", "password")
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
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


