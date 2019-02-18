import os

import pytest
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.access import AccessHandler
from tests.api.test_response import setup, LocalTestServer, StopHandler
import pymongo
import pymongo.errors

_ = setup

curr_dir = os.path.abspath(os.curdir)

ASSET_FOLDER = '../asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


class CoreApiTestServer(CoreApiContainer):
    rules = [
        (r'/kill', StopHandler),
        (r'/roles/?(.*)', RoleHandler),
        (r'/access/?(.*)', AccessHandler),
    ]


class HttpServer(LocalTestServer):

    def start(self, *args, **kwargs):
        return CoreApiTestServer


@pytest.fixture()
def http():
    server = HttpServer()
    yield server
    server.stop()


# def test_it():
#     from tornado.ioloop import IOLoop
#     role = CoreRole(
#         name="mra",
#         email="m.rau@plan-net.com",
#         password="secret",
#         perm=["mongodb://core4test", "mongodb://core3"]
#     )
#     out = IOLoop.current().run_sync(lambda: role.save())
#     assert out
#     role = CoreRole(
#         name="mbr",
#         email="test@plan-net.com",
#         password="secret",
#         perm=["mongodb://core3"]
#     )
#     out = IOLoop.current().run_sync(lambda: role.save())
#     assert out
#     out = IOLoop.current().run_sync(lambda: role.load_one(name="mra"))
#     assert out["name"] == "mra"
#     out = IOLoop.current().run_sync(lambda: role.find_one(name="mra"))
#     assert out.name == "mra"
#     manager = core4.api.v1.request.role.access.manager.CoreAccessManager("mra")
#     token_mra = manager.synchronise()
#     db = has_access("mra", token_mra["mongodb"], "core4test")
#     assert db.sys.role.count_documents({}) == 2
#     manager = core4.api.v1.request.role.access.manager.CoreAccessManager("mbr")
#     token_mbr = manager.synchronise()
#     db = has_access("mbr", token_mbr["mongodb"], "core4test")
#     with pytest.raises(pymongo.errors.OperationFailure):
#         print(db.sys.role.count_documents({}))
#     db = has_access("mbr", token_mbr["mongodb"], "test_user_db!mbr")
#     db.test1.insert_one({"hello": "world"})
#     assert db.test1.count_documents({}) == 1
#     db = has_access("mra", token_mbr["mongodb"], "test_user_db!mbr")
#     with pytest.raises(pymongo.errors.OperationFailure):
#         print(db.test1.count_documents({}))

def test_grant(http):
    data = {
        "name": "test_role1",
        "realname": "test role1",
        "password": "123456",
        "email": "test@mail.com",
        "role": [
            "standard_user"
        ],
        "perm": [
            #"mongodb://core4test"
        ]
    }
    rv = http.post("/roles", json=data)
    assert rv.status_code == 200
    id = rv.json()["data"]["_id"]
    etag = rv.json()["data"]["etag"]

    admin_token = http.token
    http.token = None
    rv = http.get("/core4/api/v1/login?username=test_role1&password=123456",
                  base=False)
    assert rv.status_code == 200
    token = rv.json()["data"]["token"]
    http.token = token

    rv = http.get("/core4/api/v1/profile", base=False)
    assert rv.status_code == 200

    rv = http.post("/access")
    assert rv.status_code == 200

    access = rv.json()["data"]["mongodb"]
    print(access)
    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test"
        ]
    }

    http.token = admin_token
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200
    etag = rv.json()["data"]["etag"]

    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    http.token = token
    rv = http.post("/access")
    assert rv.status_code == 200
    access = rv.json()["data"]["mongodb"]
    print(access)

    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    print(mongo["core4test"].list_collection_names())

    data = {
        "etag": etag,
        "realname": "no change"
    }

    http.token = admin_token
    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200
    etag = rv.json()["data"]["etag"]

    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    print(mongo["core4test"].list_collection_names())

    data = {
        "etag": etag,
        "perm": [
            "mongodb://core4test",
            "mongodb://other"
        ]
    }

    rv = http.put("/roles/" + id, json=data)
    assert rv.status_code == 200

    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    with pytest.raises(pymongo.errors.OperationFailure):
        print(mongo.server_info())
    with pytest.raises(pymongo.errors.OperationFailure):
        _ = mongo["core4test"].list_collection_names()

    http.token = token
    rv = http.post("/access/mongodb")
    assert rv.status_code == 200
    print(rv.json())
    access = rv.json()["data"]
    print(access)

    mongo = pymongo.MongoClient("mongodb://test_role1:" + access + "@localhost:27017")
    print(mongo.server_info())
    _ = mongo["core4test"].list_collection_names()
