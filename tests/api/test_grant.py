import pytest
import motor
import pymongo.errors
import core4.api.v1.request.role.field
from tests.api.test_test import setup, mongodb, core4api

_ = setup
_ = mongodb
_ = core4api


@pytest.fixture(autouse=True)
def reset_user(tmpdir, mongodb):
    ret = mongodb.client.admin.command('usersInfo')
    for user in ret["users"]:
        if user["user"].startswith("test_reg_"):
            mongodb.client.admin.command('dropUser', user["user"])


async def test_login(core4api):
    await core4api.login()
    resp = await core4api.get(
        '/core4/api/v1/profile')
    assert resp.code == 200


async def test_grant(core4api):

    async def _access(access):
        mongo = motor.MotorClient(
            "mongodb://test_reg_test_role1:" + access + "@testmongo:27017")
        _ = await mongo.server_info()
        _ = await mongo["core4test"].list_collection_names()
        assert await mongo.core4test.sys.role.count_documents({}) > 0

    async def _no_access(access):
        with pytest.raises(pymongo.errors.OperationFailure):
            await _access(access)

    await core4api.login()
    data = {
        "name": "test_reg_test_role1",
        "realname": "test role1",
        "passwd": "123456",
        "email": "test@mail.com",
        "role": [
            "standard_user"
        ],
        "perm": []
    }
    rv = await core4api.post("/core4/api/v1/roles", json=data)
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200

    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200
    access = rv.json()["data"]["mongodb"]

    await _no_access(access)

    core4api.set_admin()
    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test"
        ]
    }
    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    await _no_access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200
    access = rv.json()["data"]["mongodb"]

    await _access(access)

    data = {
        "etag": etag,
        "realname": "no change"
    }

    core4api.set_admin()
    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    await _access(access)

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test",
            "mongodb://other"
        ]
    }

    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    await _no_access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access/mongodb")
    assert rv.code == 200
    access = rv.json()["data"]

    await _access(access)

    data = {
        "etag": etag,
        "perm": [
            "mongodb://other"
        ]
    }

    core4api.set_admin()
    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    assert rv.code == 200

    await _no_access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access/mongodb")
    assert rv.code == 200
    access = rv.json()["data"]

    await _no_access(access)


async def add_user(http, username):
    http.set_admin()
    rv = await http.post("/core4/api/v1/roles",
                         json={
                             "name": username,
                             "role": ["standard_user"],
                             "email": username + "@mail.com",
                             "passwd": username
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
    await add_user(core4api, "test_reg_user1")
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
    assert rv.code == 405
    
    rv = await core4api.get("/core4/api/v1/system")
    assert rv.code == 200

    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/event/history")
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/setting")
    assert rv.code == 200


async def add_job_user(http, username, perm):
    http.set_admin()
    rv = await http.post("/core4/api/v1/roles",
                         json={
                             "name": username,
                             "role": ["standard_user"],
                             "email": username + "@mail.com",
                             "passwd": username,
                             "perm": perm
                         })
    assert rv.code == 200
    http.token = None
    conn = await http.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    http.token = conn.json()["data"]["token"]
    return http.token


async def test_enqueue(core4api):
    await core4api.login()
    await add_job_user(
        core4api, "test_reg_user1", [
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
        core4api, "test_reg_user2",
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
        rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
            "name": "core4.queue.helper.job.example.DummyJob",
            "id": i + 1
        }, headers={"Content-Type": "application/json"})
        assert rv.code == 200

    for i in range(0, 6):
        rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
            "name": "tests.api.test_grant.MyJob",
            "id": i + 1
        }, headers={"Content-Type": "application/json"})
        assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 16

    await add_job_user(core4api, "test_reg_user1", perm=[
        "api://core4.api.v1.request.queue.job.*",
        "job://core4.queue.helper.job.*/r"
    ])
    rv = await core4api.get("/core4/api/v1/jobs")
    assert rv.json()["total_count"] == 10

    core4api.set_admin()
    await add_job_user(core4api, "test_reg_user2", perm=[
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

    rv = await core4api.post("/core4/api/v1/jobs/enqueue", json={
        "name": "tests.api.test_grant.MyJob"
    }, headers={"Content-Type": "application/json"})
    assert rv.code == 403

    core4api.set_admin()
    await add_job_user(core4api, "test_reg_user4", perm=[
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
    token3 = await add_job_user(core4api, "test_reg_user3", perm=[
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

    token4 = await add_job_user(core4api, "test_reg_user4", perm=[
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
        name="test_reg_role",
        realname="test role",
        perm=["api://core4.api.v1.abc"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="test_reg_role2",
        realname="test role2",
        perm=["api://core4.api.v1.aaa"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", json=dict(
        name="test_reg_user",
        realname="test user",
        passwd="password",
        email="test@user.com",
        perm=["api://core4.api.v1.request"],
        role=["test_reg_role", "test_reg_role2"]
    ))
    assert rv.code == 200
    user_id = rv.json()["data"]["_id"]
    core4api.token = None
    await core4api.login("test_reg_user", "password")
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
    data = rv.json()["data"]
    assert data["name"] == "test_reg_user"
    assert data["_id"] == user_id
    assert data["email"] == "test@user.com"
    assert data["realname"] == "test user"
    assert data["perm"] == ['api://core4.api.v1.aaa',
                            'api://core4.api.v1.abc',
                            'api://core4.api.v1.request']
    assert data["last_login"] is not None
    assert data["is_active"]
    assert data["role"] == ['test_reg_role', 'test_reg_role2']
    assert data["token_expires"] is not None


