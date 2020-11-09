import pytest
import motor
import pymongo.errors
import time
import core4.api.v1.request.role.field
from tests.api.test_test import setup, mongodb, core4api
from tests.api.test_info import info_server

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
        """
        Check if accessing collection ons mongodb is possible, try/except is caused by
        async, otherwise tests fail randomly
        :param access:
        :return:
        """
        counter = 0

        while True:
            try:
                counter += 1
                mongo = motor.MotorClient(
                    "mongodb://test_reg_test_role1:" + access + "@testmongo:27017")
                _ = await mongo.server_info()
                _ = await mongo["core4test"].list_collection_names()
                time.sleep(1)
                break
            except pymongo.errors.OperationFailure as ops_fail:
                print(ops_fail.details['codeName'])
                time.sleep(1)
                if counter == 5:
                    break
                continue

            except Exception as E:
                print("something really strange happen: ",
                      E.details['codeName'])
                break

        assert await mongo.core4test.sys.role.count_documents({}) > 0

    async def _no_access(access):
        counter = 0
        with pytest.raises(pymongo.errors.OperationFailure):
            while True:
                try:
                    counter += 1
                    mongo = motor.MotorClient(
                        "mongodb://test_reg_test_role1:" + access + "@testmongo:27017")
                    _ = await mongo.server_info()

                    time.sleep(1)
                    break
                except pymongo.errors.OperationFailure as ops_fail:
                    print(ops_fail.details['codeName'])
                    time.sleep(1)
                    if counter == 5:
                        break
                    continue
                except Exception as E:
                    print("something really strange happen: ",
                          E.details['codeName'])
                    break
            _ = await mongo["core4test"].list_collection_names()

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
    # 1
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
    # 2
    await _access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access")
    assert rv.code == 200
    access = rv.json()["data"]["mongodb"]
    # 3
    await _access(access)

    data = {
        "etag": etag,
        "realname": "no change"
    }

    core4api.set_admin()
    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]
    # 4
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
    # 5
    await _access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access/mongodb")
    assert rv.code == 200
    access = rv.json()["data"]
    # 6
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

    # 7
    await _no_access(access)

    await core4api.login("test_reg_test_role1", "123456")
    rv = await core4api.post("/core4/api/v1/access/mongodb")
    assert rv.code == 200
    access = rv.json()["data"]

    # 8
    await _no_access(access)

    core4api.set_admin()
    rv = await core4api.get("/core4/api/v1/roles/" + id)
    # 9
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test"
        ]
    }

    rv = await core4api.put("/core4/api/v1/roles/" + id, json=data)
    # 10
    assert rv.code == 200
    etag = rv.json()["data"]["etag"]

    await _access(access)

    rv = await core4api.delete("/core4/api/v1/roles/" + id + "/" + etag)
    # 11
    assert rv.code == 200

    counter = 0
    while True:
        try:
            mongo = motor.MotorClient(
                "mongodb://test_reg_test_role1:" + access + "@testmongo:27017")
            _ = await mongo.server_info()

            time.sleep(1)
            break
        except pymongo.errors.OperationFailure as aha:
            print(aha.details['codeName'])
            time.sleep(1)
            counter += 1
            if counter == 5:
                break

    assert counter == 5
    # 12
    await _no_access(access)

    await core4api.login("test_reg_test_role1", "123456", 401)
    rv = await core4api.get("/core4/api/v1/profile")

    assert rv.code == 401


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
    assert data["perm"] == ["api://core4.api.v1.request"]

    assert data["perm_total"] == ['api://core4.api.v1.aaa',
                                  'api://core4.api.v1.abc',
                                  'api://core4.api.v1.request']
    assert data["last_login"] is not None
    assert data["is_active"]
    assert data["role"] == ['test_reg_role', 'test_reg_role2']
    assert data["token_expires"] is not None


async def add_user_method_perms(http, username, perms=""):
    http.set_admin()
    rv = await http.post("/core4/api/v1/roles",
                         json={
                             "name": username,
                             "role": ["standard_user"],
                             "email": username + "@mail.com",
                             "passwd": username,
                             "perm": ["api://core4.api.v1.request.role" + perms]
                         })
    assert rv.code == 200
    http.token = None
    conn = await http.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    http.token = conn.json()["data"]["token"]


async def test_method_permission(core4api):
    await core4api.login()
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200

    # check GET
    await add_user_method_perms(core4api, "test_reg_user1", "/r")
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles")
    assert rv.code == 403

    # check POST
    await add_user_method_perms(core4api, "test_reg_user2", "/c")
    rv = await core4api.post("/core4/api/v1/roles",
                             json={
                                 "name": "mkr",
                                 "role": ["standard_user"],
                                 "email": "mkr" + "@mail.com",
                                 "passwd": "mkr",
                                 "perm": ["api://core4.api.v1.request.role/d"]
                             })
    assert rv.code == 200
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 403

    # check PUT
    await add_user_method_perms(core4api, "test_reg_user3", "/u")
    user_id = await core4api.get("/core4/api/v1/profile")
    assert user_id.code == 200
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 403
    rv = await core4api.put("/core4/api/v1/roles/" +
                            user_id.json()["data"]["_id"],
                            json={
                                "name": "mkr2",
                                "role": ["standard_user"],
                                "email": "mkr2" + "@mail.com",
                                "passwd": "mkr2",
                                "perm": ["api://core4.api.v1.request.role/d"],
                                "etag": user_id.json()["data"]["etag"]
                            })
    assert rv.code == 200

    # check DELETE
    await add_user_method_perms(core4api, "test_perm_user4", "/d")
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 403
    user_id = await core4api.get("/core4/api/v1/profile")
    rv = await core4api.delete("/core4/api/v1/roles/" +
                               user_id.json()["data"]["_id"] +
                               "?etag=" + user_id.json()["data"]["etag"])
    assert rv.code == 200

    # check combined DELTE and GET
    await add_user_method_perms(core4api, "test_perm_user4", "/rd")
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 200
    user_id = await core4api.get("/core4/api/v1/profile")

    rv = await core4api.put("/core4/api/v1/roles/" +
                            user_id.json()["data"]["_id"],
                            json={
                                "name": "mkr2",
                                "role": ["standard_user"],
                                "email": "mkr2" + "@mail.com",
                                "passwd": "mkr2",
                                "perm": ["api://core4.api.v1.request.role/d"],
                                "etag": user_id.json()["data"]["etag"]
                            })
    assert rv.code == 403

    rv = await core4api.delete("/core4/api/v1/roles/" +
                               user_id.json()["data"]["_id"] +
                               "?etag=" + user_id.json()["data"]["etag"])
    assert rv.code == 200

    # check three combined perms
    await add_user_method_perms(core4api, "test_perm_user4", "/rcd")
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 200

    user_id = await core4api.get("/core4/api/v1/profile")

    rv = await core4api.post("/core4/api/v1/roles",
                             json={
                                 "name": "mkr4",
                                 "role": ["standard_user"],
                                 "email": "mkr4" + "@mail.com",
                                 "passwd": "mkr4",
                                 "perm": ["api://core4.api.v1.request.role/d"]
                             })
    assert rv.code == 200

    rv = await core4api.put("/core4/api/v1/roles/" +
                            user_id.json()["data"]["_id"],
                            json={
                                "name": "mkr2",
                                "role": ["standard_user"],
                                "email": "mkr2" + "@mail.com",
                                "passwd": "mkr2",
                                "perm": ["api://core4.api.v1.request.role/d"],
                                "etag": user_id.json()["data"]["etag"]
                            })
    assert rv.code == 403

    rv = await core4api.delete("/core4/api/v1/roles/" +
                               user_id.json()["data"]["_id"] +
                               "?etag=" + user_id.json()["data"]["etag"])
    assert rv.code == 200

    # test incorrect permissions
    core4api.set_admin()
    rv = await core4api.post("/core4/api/v1/roles",
                             json={
                                 "name": "error",
                                 "role": ["standard_user"],
                                 "email": "error" + "@mail.com",
                                 "passwd": "error",
                                 "perm": [
                                     "api://core4.api.v1.request.role/x"]
                             })
    assert rv.code == 400

    rv = await core4api.post("/core4/api/v1/roles",
                             json={
                                 "name": "error",
                                 "role": ["standard_user"],
                                 "email": "error" + "@mail.com",
                                 "passwd": "error",
                                 "perm": [
                                     "api://core4.api.v1.request.role/rxc"]
                             })
    assert rv.code == 400

    # test core4os specific XENTER method


async def test_grant_xmethods(info_server):
    await info_server.login()
    username = "mkrxenter"
    rv = await info_server.post("/core4/api/v1/roles",
                                json={
                                    "name": username,
                                    "role": ["standard_user"],
                                    "email": username + "@mail.com",
                                    "passwd": username,
                                    "perm": ["api://core4.api.v1.*/r",
                                             "api://test.*/r"]
                                })
    assert rv.code == 200
    info_server.token = None
    conn = await info_server.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    info_server.token = conn.json()["data"]["token"]

    rv = await info_server.get("/core4/api/v1/profile")
    assert rv.code == 200
    rv1 = await info_server.get("/core4/api/v1/_info")
    assert rv1.code == 200
    rv2 = await info_server.get("/test/_info")
    assert rv2.code == 200
    assert len(rv1.json()["data"]) == len(rv2.json()["data"])
    ih1 = [i for i in rv1.json()["data"] if "SimpleHandler" in i["qual_name"]]
    ih2 = [i for i in rv2.json()["data"] if "SimpleHandler" in i["qual_name"]]
    assert ih1 == ih2
    r1 = ih1[0]["rsc_id"]
    for mode in ("card", "help", "enter"):
        rv = await info_server._fetch("X" + mode.upper(),
                                      "/test/_info/" + mode + "/" + r1,
                                      allow_nonstandard_methods=True)
        assert rv.code == 200

    # Test with no read-permissions to the Handler,
    #
    await info_server.login()
    username = "mkrxenter_no_perms"
    rv = await info_server.post("/core4/api/v1/roles",
                                json={
                                    "name": username,
                                    "role": ["standard_user"],
                                    "email": username + "@mail.com",
                                    "passwd": username,
                                    "perm": ["api://core4.api.v1.*/r",
                                             "api://test.*/d"]
                                })
    assert rv.code == 200
    info_server.token = None
    conn = await info_server.get(
        "/core4/api/v1/login?username=" + username + "&password=" + username)
    assert conn.code == 200
    info_server.token = conn.json()["data"]["token"]

    rv = await info_server.get("/core4/api/v1/profile")
    assert rv.code == 200
    rv1 = await info_server.get("/core4/api/v1/_info")
    assert rv1.code == 200
    rv2 = await info_server.get("/test/_info")
    assert rv2.code == 200
    assert len(rv1.json()["data"]) == len(rv2.json()["data"])
    ih1 = [i for i in rv1.json()["data"] if "SimpleHandler" in i["qual_name"]]
    ih2 = [i for i in rv2.json()["data"] if "SimpleHandler" in i["qual_name"]]
    # the _info handler is only viable without any arguments.
    for mode in ("card", "help"):
        rv = await info_server._fetch("X" + mode.upper(),
                                      "/test/_info/" + mode + "/" + r1,
                                      allow_nonstandard_methods=True)
        assert rv.code == 200
    rv = await info_server._fetch("XENTER",
                                      "/test/_info/" + "enter" + "/" + r1,
                                      allow_nonstandard_methods=True)
    assert rv.code == 403

