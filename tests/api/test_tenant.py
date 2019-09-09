import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.tenant import CoreTenantHandler
from core4.api.v1.server import CoreApiServer
from tests.api.test_test import setup, mongodb, run
from core4.api.v1.request.role.main import CoreRole

_ = setup
_ = mongodb


@pytest.fixture()
def info_server():
    yield from run(
        TenantServer1,
        CoreApiServer
    )


class SimpleHandler(CoreTenantHandler):

    async def get(self, b):
        print("OK: " + str(b))
        print("CLIENT: " + self.client)
        self.reply("OK: " + str(b) + "-" + self.client)


class TenantServer1(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/named/(?P<client>.+)/(?P<b>.*)", SimpleHandler),
        (r"/unnamed/(.+)/(.*)", SimpleHandler),
    ]


async def test_access(info_server):
    role = CoreRole(
        name="myclient1",
        realname="my client 1",
        is_active=True,
        perm=[
            "app://client/client1",
            "api://tests.api.test_tenant.*",
        ]
    )
    await role.save()
    role._check_user()
    assert not role.is_user
    user = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=True,
        email="m.rau@plan-net.com",
        password="hello world",
        role=["myclient1"]
    )
    await user.save()
    user._check_user()

    await info_server.login("mra", "hello world")
    rv2 = await info_server.get("/test/named/client1/")
    assert rv2.code == 200
    rv2 = await info_server.get("/test/named/client2/abc")
    assert rv2.code == 403
    rv2 = await info_server.get("/test/unnamed/client1/")
    assert rv2.code == 200
    rv2 = await info_server.get("/test/unnamed/client1/abc")
    assert rv2.code == 200


async def test_deep_access(info_server):
    role = CoreRole(
        name="myclient1",
        realname="my client 1",
        is_active=True,
        perm=[
            "app://client/client1/unit2",
            "api://tests.api.test_tenant.*",
        ]
    )
    await role.save()
    role._check_user()
    assert not role.is_user
    user = CoreRole(
        name="mra",
        realname="Michael Rau",
        is_active=True,
        email="m.rau@plan-net.com",
        password="hello world",
        role=["myclient1"]
    )
    await user.save()
    user._check_user()

    await info_server.login("mra", "hello world")
    rv2 = await info_server.get("/test/named/client1/unit2/abc")
    assert rv2.code == 200
    assert rv2.json()["data"] == "OK: abc-client1/unit2"


