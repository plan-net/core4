import pytest

import core4.api.v1.request.role.field
from core4.api.v1.request.role.main import CoreRole
from core4.api.v1.server import CoreApiServer
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from tests.api.test_test import run, setup, mongodb
import pymongo


_ = setup
_ = mongodb

class SyncHandler(CoreRequestHandler):
    author = "mra"

    def get(self):
        coll = self.config.sys.queue.connect_sync()
        self.reply({
            "connect": str(coll),
            "collection": str(coll.connection)
        })

class AsyncHandler(CoreRequestHandler):
    author = "mra"

    def get(self):
        coll = self.config.sys.queue.connect_async()
        self.reply({
            "connect": str(coll),
            "collection": str(coll.connection)
        })


class MyContainer(CoreApiContainer):

    root = "/test"
    rules = [
        (r"/sync", SyncHandler),
        (r"/async", AsyncHandler)

    ]


@pytest.yield_fixture
def core4_test():
    yield from run(
        MyContainer,
        CoreApiServer
    )


async def test_connect(core4_test):
    await core4_test.login()
    resp = await core4_test.get(
        '/core4/api/v1/profile')
    assert resp.code == 200

    resp = await core4_test.get(
        '/test/sync')
    assert resp.code == 200
    assert "async=\'False\'" in resp.json()["data"]["connect"]
    assert resp.json()["data"]["collection"].startswith("MongoClient")

    resp = await core4_test.get(
        '/test/async')
    assert resp.code == 200
    assert "async=\'True\'" in resp.json()["data"]["connect"]
    assert resp.json()["data"]["collection"].startswith("MotorClient")
