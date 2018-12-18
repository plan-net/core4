import logging
import os

import pymongo
import pytest

import core4.api.v1.request.role.field
import core4.error
import core4.logger
import core4.queue.main
import core4.queue.worker
import core4.service.setup
import core4.util
import core4.util.crypt
import core4.util.data
import core4.util.tool
from core4.api.v1.application import CoreApiContainer
# from core4.api.v1.request.queue.job import JobSummary
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.role.model import CoreRole
from tests.api.test_response import LocalTestServer, StopHandler

ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


@pytest.fixture(autouse=True)
def setup(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_api__token__expiration"] = "!!int 60"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool True"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ["CORE4_OPTION_worker__min_free_ram"] = "!!int 32"
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    # setup = core4.service.setup.CoreSetup()
    # setup.make_role()
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


def json_decode(resp):
    return core4.util.data.json_decode(resp.body.decode("utf-8"))


class CoreApiTestServer(CoreApiContainer):
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


# @pytest.fixture()
# def loop():
#     tornado.ioloop.IOLoop.current().clear_current()
#     loop = tornado.ioloop.IOLoop()
#     loop.make_current()
#     yield loop
#     print("stop", loop, os.getpid())
#     loop.clear_current()
#     loop.close(all_fds=True)


@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)[MONGO_DATABASE]


def test_role_init():
    role = CoreRole()
    with pytest.raises(AttributeError):
        role.validate()
    CoreRole(name="mra").validate()
    with pytest.raises(TypeError):
        CoreRole(name=123).validate()
    with pytest.raises(KeyError):
        CoreRole(bla=123)


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


def test_has_mail():
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        email="m.rau@plan-net.com",
    )
    with pytest.raises(AttributeError):
        role._check_user()
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        password="hello world",
    )
    with pytest.raises(AttributeError):
        role._check_user()
    role = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=False,
        email="m.rau@plan-net.com",
        password="hello world",
    )
    role._check_user()
    core4.util.crypt.pwd_context.verify("hello world", role.password)
    role.password = "very secret"
    assert not core4.util.crypt.pwd_context.verify("hello world",
                                                   role.password)
    assert core4.util.crypt.pwd_context.verify("very secret", role.password)


def test_role(http):
    r1 = http.post("/roles", json=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert r1.status_code == 200
    r2 = http.post("/roles", json=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert r2.status_code == 200
    r3 = http.post("/roles", json=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        password="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert r3.status_code == 200

    i1 = r1.json()["data"]["_id"]
    i2 = r2.json()["data"]["_id"]
    i3 = r3.json()["data"]["_id"]

    rr1 = http.get("/roles/" + i1)
    rr2 = http.get("/roles/" + i2)
    rr3 = http.get("/roles/" + i3)
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


def test_server_test(http):
    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200


def test_init(http):
    rv = http.post("/roles")
    assert rv.json()["code"] == 400
    assert "Missing argument name" in rv.json()["error"]

    data = {}
    data["name"] = "mra"
    data["password"] = "123456"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "requires email and password" in rv.json()["error"]

    data["realname"] = "Michael Rau"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "requires email and password" in rv.json()["error"]

    data["email"] = "m.rau-plan-net.com"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "field [email] must match" in rv.json()["error"]

    data["email"] = "m.rau@plan-net.com"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200


def test_validate_name(http):
    data = {}
    data["name"] = "m r a"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["password"] = "123456"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "field [name] must match" in rv.json()["error"]


def test_validate_perm(http):
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["password"] = "123456"

    data["perm"] = "bla"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "parameter [perm] expected as_type [list]" in rv.json()["error"]

    data["perm"] = ["bla"]
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [bla]" in rv.json()["error"]

    data["perm"] = ["app:hello"]
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [app:hello]" in rv.json()["error"]

    data["perm"] = ["app:/hello"]
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [app:/hello]" in rv.json()["error"]

    data["perm"] = ["app://hello", "api:/bla"]
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "invalid permission protocol [api:/bla]" in rv.json()["error"]
    # pprint(rv.json())

    data["perm"] = ["app://hello", "api://bla"]
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200


def test_type_error(http):
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["password"] = "123456"
    data["is_active"] = "x"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "parameter [is_active] expected as_type [bool]" \
           in rv.json()["error"]


def test_create(http, mongodb):
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["password"] = "123456"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    assert mongodb.sys.role.count_documents({}) == 3
    doc = mongodb.sys.role.find_one({"name": "mra"})
    assert doc is not None


def test_duplicate_name(http):
    data = {}
    data["name"] = "mra"
    data["realname"] = "Michael Rau"
    data["email"] = "m.rau@plan-net.com"
    data["password"] = "123456"
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 400
    assert "name or email exists" in rv.json()["error"]


def test_unknown_role(http):
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "test_role2",
        "realname": "test role2",
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "mra",
        "password": "123456",
        "email": "m.rau@plan-net.com",
        "role": ["test_role1", "test_role2", "test_role3"],
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 404
    assert "role [test_role3] not found" in rv.json()["error"]


def test_known_role(http):
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "test_role2",
        "realname": "test role2",
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    data = {
        "name": "mra",
        "password": "123456",
        "email": "m.rau@plan-net.com",
        "role": ["test_role1", "test_role2"],
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200


def test_get(http):
    names = ['Elfriede', 'Gerda', 'Ursula', 'Erna', 'Hildegard', 'Irmgard',
             'Ilse', 'Edith', 'Lieselotte', 'Gertrud']
    for i in range(1, 11):
        data = {
            "name": "test_role_%03d" % i,
            "realname": names.pop(0),
        }
        rv = http.post("/roles", json=data)
        assert rv.json()["code"] == 200
    rv = http.get("/roles?per_page=4&sort_by=realname&sort_order=-1")
    assert rv.status_code == 200
    # pprint(rv.json())
    ret = rv.json()
    assert ret["page"] == 0
    assert ret["per_page"] == 4
    assert ret["total_count"] == 12
    assert ret["page_count"] == 3
    names = []
    oid = []
    for i in range(4):
        rv = http.get("/roles?per_page=4&sort=realname&order=-1"
                      "&page=%d" % i)
        names += [i["realname"] for i in rv.json()["data"]]
        oid += [i["_id"] for i in rv.json()["data"]]
        assert rv.status_code == 200
    assert names == sorted(names, reverse=True)

    rv = http.get("/roles/" + oid[0])
    assert rv.status_code == 200
    ret = rv.json()["data"]
    assert ret["name"] == "standard_user"
    assert ret["_id"] == oid[0]
    assert "password" not in ret


def test_empty(http):
    rv = http.get('/roles?per_page=4&sort_by=realname&sort_order=-1'
                  '&filter={"name": {"$ne": "admin"}}')
    assert rv.status_code == 200
    ret = rv.json()
    assert ret["page"] == 0
    assert ret["per_page"] == 4
    assert ret["total_count"] == 1
    assert ret["page_count"] == 1
    oid = "5be414ccde8b69542b70f4d7"
    rv = http.get('/roles/' + oid)
    assert rv.status_code == 404


def test_delete(http):
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = http.post("/roles", json=data)
    id1 = rv.json()["data"]["_id"]
    etag1 = rv.json()["data"]["etag"]
    assert rv.json()["code"] == 200
    data = {
        "name": "test_role2",
        "realname": "test role2",
        "role": ["test_role1"]
    }
    rv = http.post("/roles", json=data)
    assert rv.json()["code"] == 200
    id2 = rv.json()["data"]["_id"]
    etag2 = rv.json()["data"]["etag"]
    rv = http.get("/roles/" + id2)
    assert rv.json()["code"] == 200
    assert rv.json()["data"]["role"] == ["test_role1"]
    rv = http.delete("/roles/" + id1 + "?etag=" + etag1)
    assert rv.json()["code"] == 200
    rv = http.get("/roles/" + id2)
    assert rv.json()["code"] == 200
    assert rv.json()["data"]["role"] == []
    rv = http.delete("/roles/" + id2, json={"etag": etag2})
    assert rv.json()["code"] == 200
    rv = http.get("/roles/" + id2)
    assert rv.json()["code"] == 404
    rv = http.delete("/roles/" + id2)
    assert rv.json()["code"] == 400
    assert "MissingArgumentError" in rv.json()["error"]
    rv = http.delete("/roles/" + id2 + "?etag=" + etag2)
    assert rv.json()["code"] == 404


def test_access(http):
    data = {
        "name": "user",
        "realname": "test role1",
        "email": "user@mail.com",
        "password": "123456",
        "perm": ["api://core4.api.v1.request.standard"]
    }
    rv = http.post("/roles", json=data)
    assert rv.status_code == 200
    admin_token = http.token
    http.token = None
    rv = http.get("/core4/api/v1/login?username=user&password=123456",
                  base=False)
    assert rv.status_code == 200
    token = rv.json()["data"]["token"]
    http.token = token
    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200
    etag1 = rv.json()["data"]["etag"]
    rv = http.get("/roles")
    assert rv.status_code == 403
    data = {
        "realname": "preferred name"
    }
    rv = http.put("/core4/api/v1/profile", json=data, base=False)
    assert rv.status_code == 400
    assert "MissingArgumentError" in rv.json()["error"]

    data["etag"] = etag1
    rv = http.put("/core4/api/v1/profile", json=data, base=False)
    assert rv.status_code == 200

    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200
    etag2 = rv.json()["data"]["etag"]
    assert rv.json()["data"]["realname"] == "preferred name"
    assert etag1 != etag2

    data = {
        "password": "hello",
        "etag": etag2
    }
    rv = http.put("/core4/api/v1/profile", json=data, base=False)
    assert rv.status_code == 200
    etag3 = rv.json()["data"]["etag"]

    http.token = None
    rv = http.get("/core4/api/v1/login?username=user&password=123456",
                  base=False)
    assert rv.status_code == 401
    rv = http.get("/core4/api/v1/login?username=user&password=hello",
                  base=False)
    assert rv.status_code == 200
    token = rv.json()["data"]["token"]
    http.token = token
    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200

    data = {
        "name": "user2",
        "realname": "test role1",
        "email": "user@mail.com",
        "password": "123456",
    }
    http.token = admin_token
    rv = http.post("/roles", json=data)
    assert rv.status_code == 400
    assert "mail exists" in rv.json()["error"]

    data = {
        "name": "user2",
        "realname": "test role1",
        "email": "user2@mail.com",
        "password": "123456",
    }
    rv = http.post("/roles", json=data)
    assert rv.status_code == 200

    data = {
        "email": "user2@mail.com",
        "etag": etag3
    }
    http.token = token
    rv = http.put("/core4/api/v1/profile", json=data, base=False)
    assert rv.status_code == 400
    assert "mail exists" in rv.json()["error"]

    data["email"] = "user3@mail.com"
    rv = http.put("/core4/api/v1/profile", json=data, base=False)
    assert rv.status_code == 200


def test_update(http):
    data = {
        "name": "test_role1",
        "realname": "test role1",
    }
    rv = http.post("/roles", json=data)
    assert rv.status_code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 400
    assert "MissingArgumentError" in rv.json()["error"]

    data["etag"] = etag
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200
    assert rv.json()["data"] == "no changes"

    data["realname"] = "test role one"
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200
    assert rv.json()["data"]["realname"] == "test role one"
    etag = rv.json()["data"]["etag"]

    rv = http.get("/roles/" + id)
    assert rv.status_code == 200
    assert rv.json()["data"]["realname"] == "test role one"
    assert rv.json()["data"]["etag"] == etag

    data = {
        "name": "admin",
        "etag": etag
    }
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 400
    assert "exists" in rv.json()["error"]

    data = {
        "name": "admin2",
        "etag": etag
    }
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200

    rv = http.get("/roles")
    assert rv.status_code == 200
    assert sorted([r["name"] for r in rv.json()["data"]]) == [
        "admin", "admin2", "standard_user"]


def test_update2(http):
    rv = http.post("/roles", json=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        password="123456"
    ))
    assert rv.status_code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]
    rv = http.put("/roles/" + id, json={"password": "654321", "etag": etag,
                                        "perm": ["api://core4.*"]})
    assert rv.status_code == 200

    admin_token = http.token
    http.token = None

    rv = http.get("/core4/api/v1/profile?username=mra&password=654321",
                  base=False)
    assert rv.status_code == 200
    etag2 = rv.json()["data"]["etag"]

    http.token = admin_token
    rv = http.put("/roles/" + id, json={"password": "666999666",
                                        "etag": etag2,
                                        "perm": ["app://update"]})
    assert rv.status_code == 200

    http.token = None
    rv = http.get("/core4/api/v1/login?username=mra&password=666999666",
                  base=False)
    assert rv.status_code == 200


def test_update_conflict(http):
    rv = http.post("/roles", json=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        password="123456"
    ))
    assert rv.status_code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    rv = http.put("/roles/" + id, json={"password": "654321", "etag": etag})
    assert rv.status_code == 200

    rv = http.put("/roles/" + id, json={"password": "654321", "etag": etag})
    assert rv.status_code == 400
    assert "with etag" in rv.json()["error"]


def test_delete2(http):
    rv = http.post("/roles", json=dict(
        name="mra",
        realname="Michael Rau",
        email="m.rau@plan-net.com",
        password="123456"
    ))
    assert rv.status_code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    rv = http.put("/roles/" + id, json={"password": "654321", "etag": etag})
    assert rv.status_code == 200
    etag2 = rv.json()["data"]["etag"]

    rv = http.delete("/roles/" + id, json={"etag": etag})
    assert rv.status_code == 400
    assert "with etag" in rv.json()["error"]

    rv = http.delete("/roles/" + id, json={"etag": etag2})
    assert rv.status_code == 200

    rv = http.delete("/roles/" + id, json={"etag": etag})
    assert rv.status_code == 404


def test_recursive_delete(http):
    rv = http.post("/roles", json=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert rv.status_code == 200
    rv = http.post("/roles", json=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert rv.status_code == 200
    rv = http.post("/roles", json=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        password="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert rv.status_code == 200

    rv = http.get('/roles?filter={"name": "test_role3"}')
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 1
    assert rv.json()["data"][0]["perm"] == ['app://3']
    id3 = rv.json()["data"][0]["_id"]

    rv = http.get('/roles/' + id3)
    assert rv.status_code == 200
    assert rv.json()["data"]["perm"] == ['app://1', 'app://2', 'app://3']
    assert rv.json()["data"]["role"] == ['test_role1', 'test_role2']

    rv = http.get('/roles?filter={"name": "test_role1"}')
    assert rv.status_code == 200
    etag1 = rv.json()["data"][0]["etag"]
    id1 = rv.json()["data"][0]["_id"]
    rv = http.delete('/roles/' + id1 + '?etag=' + etag1)
    assert rv.status_code == 200

    rv = http.get('/roles/' + id3)
    assert rv.status_code == 200
    assert rv.json()["data"]["perm"] == ['app://2', 'app://3']
    assert rv.json()["data"]["role"] == ['test_role2']

    rv = http.get('/roles?filter={"name": "test_role2"}')
    assert rv.status_code == 200
    assert len(rv.json()["data"]) == 1
    assert rv.json()["data"][0]["perm"] == ['app://2']
    id2 = rv.json()["data"][0]["_id"]

    rv = http.get('/roles/' + id2)
    assert rv.status_code == 200

    assert rv.json()["data"]["perm"] == ['app://2']
    assert rv.json()["data"]["role"] == []


def test_recursion(http):
    rv = http.post("/roles", json=dict(
        name="test_role1",
        realname="test role 1",
        perm=["app://1"]
    ))
    assert rv.status_code == 200
    r1 = rv.json()["data"]
    rv = http.post("/roles", json=dict(
        name="test_role2",
        realname="test role 2",
        role=["test_role1"],
        perm=["app://2"]
    ))
    assert rv.status_code == 200
    r2 = rv.json()["data"]
    rv = http.post("/roles", json=dict(
        name="test_role3",
        realname="test role 3",
        email="m.rau@plan-net.com",
        password="hello world",
        role=["test_role1", "test_role2"],
        perm=["app://3"]
    ))
    assert rv.status_code == 200
    r3 = rv.json()["data"]

    rv = http.put("/roles" + r1["_id"], json=dict(
        role=["test_role2", "test_role3"],
        etag=r1["etag"]
    ))
    assert rv.status_code == 200

    rv = http.put("/roles" + r3["_id"], json=dict(
        role=["test_role1", "test_role2"],
        etag=r3["etag"]
    ))
    assert rv.status_code == 200
    assert rv.json()["data"] == "no changes"

    rv = http.put("/roles" + r3["_id"], json=dict(
        role=["test_role1", "test_role2", "test_role3", "test_role3"],
        etag=r3["etag"]
    ))
    assert rv.status_code == 200

    rv = http.get("/roles" + r3["_id"])
    assert rv.status_code == 200
    assert rv.json()["data"]["role"] == [
        'test_role1', 'test_role2']
    etag = rv.json()["data"]["etag"]

    rv = http.get("/roles" + r1["_id"])
    assert rv.status_code == 200
    assert rv.json()["data"]["role"] == [
        'test_role2', 'test_role3']

    rv = http.put("/roles" + r3["_id"], json=dict(
        role=["test_role1", "test_role2", "test_role2"],
        etag=etag
    ))
    assert rv.status_code == 200

    rv = http.get("/roles" + r1["_id"])
    assert rv.status_code == 200
    assert rv.json()["data"]["role"] == ['test_role2', 'test_role3']

    # test1 = loop.run_sync(lambda: CoreRole.find_one(name="test_role1"))
    # assert test1.role == ['test_role2', 'test_role3']
    # assert loop.run_sync(test1.casc_perm) == ['app://1', 'app://2', 'app://3']
    #


