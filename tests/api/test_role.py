import pytest

import core4.api.v1.request.role.field
from core4.api.v1.request.role.main import CoreRole
from tests.api.test_test import setup, mongodb, core4api

_ = setup
_ = mongodb
_ = core4api


async def test_login(core4api):
    await core4api.login()
    resp = await core4api.get(
        '/core4/api/v1/profile')
    assert resp.code == 200


def test_role_init():
    role = CoreRole()
    with pytest.raises(AttributeError):
        role.validate()
    CoreRole(name="mra").validate()
    with pytest.raises(TypeError):
        CoreRole(name=123).validate()
    with pytest.raises(KeyError):
        CoreRole(bla=123)

async def test_auth_delegation(core4api):
    URL = '/core4/api/v1/login'
    resp = await core4api.get(URL + '?username=admin&password=hans')
    assert resp.code == 200
    cookie = list(resp.cookie().values())
    header = {"Cookie": "token=" + cookie[0].coded_value}
    resp = await core4api.get(URL, headers=header)
    data = {}
    data["name"] = "mkr"
    data["realname"] = "Markus Kral"
    data["email"] = "test@test.de"
    data["passwd"] = "test"
    rv = await core4api.post("/core4/api/v1/roles", headers=header, body=data)
    assert rv.json()["code"] == 200


def test_perm_validate():
    p = core4.api.v1.request.role.field.PermField(key="perm",
                                                  perm="app://test")
    with pytest.raises(TypeError):
        p.validate_type()
    p = core4.api.v1.request.role.field.PermField(key="perm",
                                                  perm=["app:/test"])
    with pytest.raises(AttributeError):
        p.validate_value()
    p = core4.api.v1.request.role.field.PermField(key="perm",
                                                  perm=["app://test",
                                                        "api://bla.bli.blub"])
    p.validate_type()
    p.validate_value()
    p = core4.api.v1.request.role.field.PermField(key="perm",
                                                  perm=["bla://test"])
    with pytest.raises(AttributeError):
        p.validate_value()

    p = core4.api.v1.request.role.field.PermField(key="perm",
                                                  perm=["mongodb://test"])
    p.validate_type()
    p.validate_value()


def test_has_mail():
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        email="m.rau@plan-net.com",
    )
    with pytest.raises(AttributeError):
        role._check_user()
    assert not role.is_user
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        password="hello world",
    )
    with pytest.raises(AttributeError):
        role._check_user()
    assert not role.is_user
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        email="m.rau@plan-net.com",
        password="hello world",
    )
    role._check_user()
    assert role.is_user
    core4.util.crypt.pwd_context.verify("hello world", role.password)
    role.password = "very secret"
    assert not core4.util.crypt.pwd_context.verify("hello world",
                                                   role.password)
    assert core4.util.crypt.pwd_context.verify("very secret", role.password)


async def test_role(core4api):
    await core4api.login()

    r1 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert r1.code == 200

    r2 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert r2.code == 200

    r3 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        passwd="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert r3.code == 200

    i1 = r1.json()["data"]["_id"]
    i2 = r2.json()["data"]["_id"]
    i3 = r3.json()["data"]["_id"]

    rr1 = await core4api.get("/core4/api/v1/roles/" + i1)
    rr2 = await core4api.get("/core4/api/v1/roles/" + i2)
    rr3 = await core4api.get("/core4/api/v1/roles/" + i3)

    assert rr1.json()["data"]["perm"] == ['app://1']
    assert rr2.json()["data"]["perm"] == ['app://1', 'app://2']
    assert rr3.json()["data"]["perm"] == ['app://1', 'app://2', 'app://3']


def test_comparison():
    r1 = CoreRole(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    )
    r2 = CoreRole(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    )
    assert r1 == r2
    r3 = CoreRole(
        name="test_role2",
        realname="test role 1",
        perm=["app://1"]
    )
    assert r1 != r3
    assert r2 != r3
    assert r1 < r3
    assert r2 < r3


async def test_server_test(core4api):
    await CoreRole(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ).save()
    await CoreRole(
        name="test_role2",
        realname="test role 1",
        perm=["app://1"]
    ).save()
    await core4api.login()
    r1 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        passwd="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert r1.code == 200

    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200


async def test_init(core4api):
    await core4api.login()

    rv = await core4api.post("/core4/api/v1/roles")
    assert rv.json()["code"] == 400
    assert "Missing argument name" in rv.json()["error"]

    data = {}
    data["name"] = "mra"
    data["passwd"] = "123456"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "requires email on creation" in rv.json()["error"]

    data["realname"] = "Michael Rau"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "requires email on creation" in rv.json()["error"]

    data["email"] = "m.rau-plan-net.com"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "field [email] must match" in rv.json()["error"]

    data["email"] = "m.rau@plan-net.com"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200


async def test_validate_name(core4api):
    await core4api.login()
    data = {}
    data["name"] = "m r a"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["passwd"] = "123456"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "field [name] must match" in rv.json()["error"]


async def test_validate_perm(core4api):
    await core4api.login()
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["passwd"] = "123456"

    data["perm"] = "bla"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "parameter [perm] expected as_type [list]" in rv.json()["error"]

    data["perm"] = ["bla"]
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [bla]" in rv.json()["error"]

    data["perm"] = ["app:hello"]
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [app:hello]" in rv.json()["error"]

    data["perm"] = ["app:/hello"]
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [app:/hello]" in rv.json()["error"]

    data["perm"] = ["app://hello", "api:/bla"]
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [api:/bla]" in rv.json()["error"]

    data["perm"] = ["app://hello", "api://bla"]
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200


async def test_type_error(core4api):
    await core4api.login()
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["passwd"] = "123456"
    data["is_active"] = "x"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "parameter [is_active] expected as_type [bool]" \
           in rv.json()["error"]


async def test_create(core4api, mongodb):
    await core4api.login()
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["passwd"] = "123456"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200
    assert mongodb.sys.role.count_documents({}) == 3
    doc = mongodb.sys.role.find_one({"name": "mra"})
    assert doc is not None


async def test_duplicate_name(core4api):
    await core4api.login()
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["passwd"] = "123456"
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 400
    assert "name or email exists" in rv.json()["error"]


async def test_unknown_role(core4api):
    await core4api.login()
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "test_role2",
        "realname": "test role2",
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "mra",
        "passwd": "123456",
        "email": "m.rau@plan-net.com",
        "role": ["test_role1", "test_role2", "test_role3"],
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 404
    assert "role [test_role3] not found" in rv.json()["error"]


async def test_get(core4api):
    await core4api.login()
    names = ['Elfriede', 'Gerda', 'Ursula', 'Erna', 'Hildegard', 'Irmgard',
             'Ilse', 'Edith', 'Lieselotte', 'Gertrud']
    for i in range(1, 11):
        data = {
            "name": "test_role_%03d" % i,
            "realname": names.pop(0),
        }
        rv = await core4api.post("/core4/api/v1/roles", body=data)
        assert rv.json()["code"] == 200
    rv = await core4api.get(
        "/core4/api/v1/roles?per_page=4&sort=realname&order=-1")
    assert rv.code == 200
    ret = rv.json()
    assert ret["page"] == 0
    assert ret["per_page"] == 4
    assert ret["total_count"] == 12
    assert ret["page_count"] == 3
    names = []
    oid = []
    for i in range(4):
        rv = await core4api.get(
            "/core4/api/v1/roles?per_page=4&page=%d&sort=realname&order=-1" % i)
        assert rv.code == 200
        names += [i["realname"] for i in rv.json()["data"]]
        oid += [i["_id"] for i in rv.json()["data"]]
    print(names)
    assert names == sorted(names, reverse=True)

    rv = await core4api.get("/core4/api/v1/roles/" + oid[0])
    assert rv.code == 200
    ret = rv.json()["data"]
    assert ret["name"] == "standard_user"
    assert ret["_id"] == oid[0]
    assert "password" not in ret


async def test_empty(core4api):
    await core4api.login()
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=4&sort=realname'
        '&order=-1&filter={"name": {"$ne": "admin"}}')
    assert rv.code == 200
    ret = rv.json()
    oid = rv.json()["data"][0]["_id"]
    assert ret["page"] == 0
    assert ret["per_page"] == 4
    assert ret["total_count"] == 1
    assert ret["page_count"] == 1
    rv = await core4api.get("/core4/api/v1/roles/" + oid)
    assert rv.code == 200
    oid = "5be414ccde8b69542b70f4d7"
    rv = await core4api.get("/core4/api/v1/roles/" + oid)
    assert rv.code == 404


async def test_nested_regex(core4api):
    await core4api.login()
    names = ['Liese', 'Lisa', 'Lieselotte', 'Hans']
    for i in range(1, 4):
        data = {
            "name": "test_role_%03d" % i,
            "realname": names.pop(0),
        }
        rv = await core4api.post("/core4/api/v1/roles", body=data)
        assert rv.json()["code"] == 200
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=3&sort=realname&order=-1'
        '&filter={"realname": {"$in": ["Li*"]}}'
    )
    assert rv.code == 200
    ret = rv.json()
    assert ret["total_count"] == 3
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=3&sort=realname&order=-1'
        '&filter={"realname": {"$in": ["Liese"]}}'
    )
    assert rv.code == 200
    ret = rv.json()
    assert rv.code == 200
    assert ret["total_count"] == 1
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=3&sort=realname&order=-1'
        '&filter={"realname": {"$in": ["L*"]}, "name": "test_role_001"}'
    )
    assert rv.code == 200
    ret = rv.json()
    assert rv.code == 200
    assert ret["total_count"] == 1
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=3&sort=realname&order=-1'
        '&filter={"realname": {"$in": ["Lies*", "Lisa"]}}'
    )
    assert rv.code == 200
    ret = rv.json()
    assert rv.code == 200
    assert ret["total_count"] == 3
    rv = await core4api.get(
        '/core4/api/v1/roles?per_page=10&sort=realname&order=-1'
        '&filter={"$and":[{"realname":{"$in": ["Li*"]}}, '
        '{"realname":{"$ne":"Lisa"}}]}'
    )
    assert rv.code == 200
    ret = rv.json()
    assert rv.code == 200
    assert ret["total_count"] == 2


async def test_delete(core4api):
    await core4api.login()
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    id1 = rv.json()["data"]["_id"]
    etag1 = rv.json()["data"]["etag"]
    assert rv.json()["code"] == 200
    data = {
        "name": "test_role2",
        "realname": "test role2",
        "role": ["test_role1"]
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.json()["code"] == 200
    id2 = rv.json()["data"]["_id"]
    etag2 = rv.json()["data"]["etag"]
    rv = await core4api.get("/core4/api/v1/roles/" + id2)
    assert rv.json()["code"] == 200
    assert rv.json()["data"]["role"] == ["test_role1"]
    rv = await core4api.delete("/core4/api/v1/roles/" + id1 + "?etag=" + etag1)
    assert rv.json()["code"] == 200
    rv = await core4api.get("/core4/api/v1/roles/" + id2)
    assert rv.json()["code"] == 200
    assert rv.json()["data"]["role"] == []
    rv = await core4api.delete("/core4/api/v1/roles/" + id2 + "/" + etag2)
    assert rv.json()["code"] == 200
    rv = await core4api.get("/core4/api/v1/roles/" + id2)
    assert rv.json()["code"] == 404
    rv = await core4api.delete("/core4/api/v1/roles/" + id2)
    assert rv.json()["code"] == 400
    assert "MissingArgumentError" in rv.json()["error"]
    rv = await core4api.delete("/core4/api/v1/roles/" + id2 + "?etag=" + etag2)
    assert rv.json()["code"] == 404


async def test_access(core4api):
    await core4api.login()
    data = {
        "name": "user",
        "realname": "test role1",
        "email": "user@mail.com",
        "passwd": "123456",
        "perm": ["api://core4.api.v1.request.standard"]
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.code == 200
    admin_token = core4api.token
    core4api.token = None
    rv = await core4api.get(
        "/core4/api/v1/login?username=user&password=123456")
    assert rv.code == 200
    token = rv.json()["data"]["token"]
    core4api.token = token
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
    etag1 = rv.json()["data"]["etag"]
    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 403
    data = {
        "realname": "preferred name"
    }
    rv = await core4api.put("/core4/api/v1/profile", body=data)
    assert rv.code == 400
    assert "MissingArgumentError" in rv.json()["error"]

    data["etag"] = etag1
    rv = await core4api.put("/core4/api/v1/profile", body=data)
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200
    etag2 = rv.json()["data"]["etag"]
    assert rv.json()["data"]["realname"] == "preferred name"
    assert etag1 != etag2

    data = {
        "passwd": "hello",
        "etag": etag2
    }
    rv = await core4api.put("/core4/api/v1/profile", body=data)
    assert rv.code == 200
    etag3 = rv.json()["data"]["etag"]

    core4api.token = None
    rv = await core4api.get(
        "/core4/api/v1/login?username=user&password=123456")
    assert rv.code == 401
    rv = await core4api.get("/core4/api/v1/login?username=user&password=hello")
    assert rv.code == 200
    token = rv.json()["data"]["token"]
    core4api.token = token
    rv = await core4api.get("/core4/api/v1/profile")
    assert rv.code == 200

    data = {
        "name": "user2",
        "realname": "test role1",
        "email": "user@mail.com",
        "passwd": "123456",
    }
    core4api.token = admin_token
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.code == 400
    assert "mail exists" in rv.json()["error"]

    data = {
        "name": "user2",
        "realname": "test role1",
        "email": "user2@mail.com",
        "passwd": "123456",
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.code == 200

    data = {
        "email": "user2@mail.com",
        "etag": etag3
    }
    core4api.token = token
    rv = await core4api.put("/core4/api/v1/profile", body=data)
    assert rv.code == 400
    assert "mail exists" in rv.json()["error"]

    data["email"] = "user3@mail.com"
    rv = await core4api.put("/core4/api/v1/profile", body=data)
    assert rv.code == 200


async def test_update(core4api):
    await core4api.login()
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = await core4api.post("/core4/api/v1/roles", body=data)
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 400
    assert "MissingArgumentError" in rv.json()["error"]

    data["etag"] = etag
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200
    assert rv.json()["data"] == "no changes"

    data["realname"] = "test role one"
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200
    assert rv.json()["data"]["realname"] == "test role one"
    etag = rv.json()["data"]["etag"]

    rv = await core4api.get("/core4/api/v1/roles/" + id)
    assert rv.code == 200
    assert rv.json()["data"]["realname"] == "test role one"
    assert rv.json()["data"]["etag"] == etag

    data = {
        "name": "admin",
        "etag": etag
    }
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 400
    assert "exists" in rv.json()["error"]

    data = {
        "name": "admin2",
        "etag": etag
    }
    rv = await core4api.put("/core4/api/v1/roles/" + id, body=data)
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/roles")
    assert rv.code == 200
    assert sorted([r["name"] for r in rv.json()["data"]]) == [
        "admin", "admin2", "standard_user"]


async def test_update2(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        passwd="123456"
    ))
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    rv = await core4api.put("/core4/api/v1/roles/" + id,
                            body={"passwd": "654321", "etag": etag,
                                  "perm": ["api://core4.*"]})
    assert rv.code == 200

    admin_token = core4api.token
    core4api.token = None

    rv = await core4api.get(
        "/core4/api/v1/profile?username=mra&password=654321")
    assert rv.code == 200
    etag2 = rv.json()["data"]["etag"]

    core4api.token = admin_token
    rv = await core4api.put(
        "/core4/api/v1/roles/" + id,
        body={
            "passwd": "666999666",
            "etag": etag2, "perm": ["app://update"]
        }
    )
    assert rv.code == 200
    core4api.token = None
    rv = await core4api.get(
        "/core4/api/v1/login?username=mra&password=666999666")
    assert rv.code == 200


async def test_update_conflict(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        passwd="123456"
    ))
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    rv = await core4api.put("/core4/api/v1/roles/" + id,
                            body={"passwd": "654321", "etag": etag})
    assert rv.code == 200

    rv = await core4api.put("/core4/api/v1/roles/" + id,
                            body={"passwd": "654321", "etag": etag})
    assert rv.code == 400
    assert "with etag" in rv.json()["error"]


async def test_delete2(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        passwd="123456"
    ))
    assert rv.code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    rv = await core4api.put("/core4/api/v1/roles/" + id,
                            body={"passwd": "654321", "etag": etag})
    assert rv.code == 200
    etag2 = rv.json()["data"]["etag"]

    rv = await core4api.delete("/core4/api/v1/roles/" + id + "/" + etag)
    assert rv.code == 400
    assert "with etag" in rv.json()["error"]

    rv = await core4api.delete("/core4/api/v1/roles/" + id + "/" + etag2)
    assert rv.code == 200

    rv = await core4api.delete("/core4/api/v1/roles/" + id + "/" + etag)
    assert rv.code == 404


async def test_recursive_delete(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        passwd="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert rv.code == 200

    rv = await core4api.get(
        '/core4/api/v1/roles?filter={"name": "test_role3"}')
    assert rv.code == 200
    assert len(rv.json()["data"]) == 1
    assert rv.json()["data"][0]["perm"] == ['app://3']
    id3 = rv.json()["data"][0]["_id"]

    rv = await core4api.get('/core4/api/v1/roles/' + id3)
    assert rv.code == 200
    assert rv.json()["data"]["perm"] == ['app://1', 'app://2', 'app://3']
    assert rv.json()["data"]["role"] == ['test_role1', 'test_role2']

    rv = await core4api.get(
        '/core4/api/v1/roles?filter={"name": "test_role1"}')
    assert rv.code == 200
    etag1 = rv.json()["data"][0]["etag"]
    id1 = rv.json()["data"][0]["_id"]
    rv = await core4api.delete('/core4/api/v1/roles/' + id1 + '?etag=' + etag1)
    assert rv.code == 200

    rv = await core4api.get('/core4/api/v1/roles/' + id3)
    assert rv.code == 200
    assert rv.json()["data"]["perm"] == ['app://2', 'app://3']
    assert rv.json()["data"]["role"] == ['test_role2']

    rv = await core4api.get(
        '/core4/api/v1/roles?filter={"name": "test_role2"}')
    assert rv.code == 200
    assert len(rv.json()["data"]) == 1
    assert rv.json()["data"][0]["perm"] == ['app://2']
    id2 = rv.json()["data"][0]["_id"]

    rv = await core4api.get('/core4/api/v1/roles/' + id2)
    assert rv.code == 200

    assert rv.json()["data"]["perm"] == ['app://2']
    assert rv.json()["data"]["role"] == []


async def test_recursion(core4api):
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert rv.code == 200
    r1 = rv.json()["data"]
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert rv.code == 200
    r2 = rv.json()["data"]
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        passwd="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert rv.code == 200
    r3 = rv.json()["data"]

    rv = await core4api.put("/core4/api/v1/roles/" + r1["_id"], body=dict(
        role=["test_role2", "test_role3"],
        etag=r1["etag"]
    ))
    assert rv.code == 200

    rv = await core4api.put("/core4/api/v1/roles/" + r3["_id"], body=dict(
        role=["test_role1", "test_role2"],
        etag=r3["etag"]
    ))
    assert rv.code == 200
    assert rv.json()["data"] == "no changes"

    rv = await core4api.put("/core4/api/v1/roles/" + r3["_id"], body=dict(
        role=["test_role1", "test_role2", "test_role3", "test_role3"],
        etag=r3["etag"]
    ))
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/roles/" + r3["_id"])
    assert rv.code == 200
    assert rv.json()["data"]["role"] == [
        'test_role1', 'test_role2']
    etag = rv.json()["data"]["etag"]

    rv = await core4api.get("/core4/api/v1/roles/" + r1["_id"])
    assert rv.code == 200
    assert rv.json()["data"]["role"] == [
        'test_role2', 'test_role3']

    rv = await core4api.put("/core4/api/v1/roles/" + r3["_id"], body=dict(
        role=["test_role1", "test_role2", "test_role2"],
        etag=etag
    ))
    assert rv.code == 200

    rv = await core4api.get("/core4/api/v1/roles/" + r1["_id"])
    assert rv.code == 200
    assert rv.json()["data"]["role"] == ['test_role2', 'test_role3']

    # test1 = loop.run_sync(lambda: CoreRole.find_one(name="test_role1"))
    # assert test1.role == ['test_role2', 'test_role3']
    # assert loop.run_sync(test1.casc_perm) == ['app://1', 'app://2', 'app://3']
async def test_cookie_create(core4api):
    """
    Test to create a user using a cookie for authentication.
    core4api.login sets the authorization-header,  so both ways of creating a
    user are tested.
    A user requires an email and a password, if creating a user while
    authenticating via url-parameters or body-parameters the  password will get
    overwritten. One cannot create a user any longer.
    :param core4api: core4api
    """
    URL = '/core4/api/v1/login'
    resp = await core4api.get(URL + '?username=admin&password=hans')
    assert resp.code == 200
    cookie = list(resp.cookie().values())
    header = {"Cookie": "token=" + cookie[0].coded_value}
    data = {}
    data["name"] = "mkr"
    data["realname"] = "Markus Kral"
    data["email"] = "test@test.de"
    data["passwd"] = "test"
    rv = await core4api.post("/core4/api/v1/roles", headers=header, body=data)
    assert rv.json()["code"] == 200
