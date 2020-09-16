import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.standard.static import CoreStaticFileHandler
from core4.api.v1.server import CoreApiServer
from tests.api.test_test import setup, mongodb, run
import core4
from pprint import pprint

_ = setup
_ = mongodb


@pytest.fixture()
def info_server():
    yield from run(
        InfoServer1,
        InfoServer2,
        CoreApiServer
    )


class SimpleHandler(CoreRequestHandler):

    title = "Simple Handler"
    async def get(self):
        self.reply("OK")


class LinkHandler1(CoreRequestHandler):
    enter_url = "http://www.google.de"
    title = "goto"


class InfoServer1(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/simple", SimpleHandler),
        (r"/google", LinkHandler1, {"title": "goto google"}),
        (r"/g", LinkHandler1, {"enter_url": "http://uni-xxx.de"}),
        (r"/info", CoreStaticFileHandler,
         {"path": "static/", "title": "static info"}),
    ]


class InfoServer2(CoreApiContainer):
    root = "/test2"
    rules = [
        (r"/simple", SimpleHandler),
        (r"/google", LinkHandler1),
        (r"/g", LinkHandler1, {"enter_url": "http://uni-m.de"}),

    ]


async def test_simple(info_server):
    await info_server.login()
    rv = await info_server.get("/core4/api/v1/profile")
    assert rv.code == 200
    rv1 = await info_server.get("/core4/api/v1/_info?search=!&per_page=1000")
    assert rv1.code == 200
    rv2 = await info_server.get("/test/_info?search=!&per_page=1000")
    assert rv2.code == 200
    assert len(rv1.json()["data"]) == len(rv2.json()["data"])
    ih1 = [i for i in rv1.json()["data"] if "SimpleHandler" in i["qual_name"]]
    ih2 = [i for i in rv2.json()["data"] if "SimpleHandler" in i["qual_name"]]
    assert ih1 == ih2
    pprint(ih1)
    r1 = ih1[0]["rsc_id"]
    for mode in ("card", "help", "enter"):
        rv = await info_server.get("/test/_info/" + mode + "/" + r1)
        assert rv.code == 200
        rv = await info_server.get("/core4/api/v1/_info/" + mode + "/" + r1)
        assert rv.code == 404


async def get_info(server, qn, key="qual_name"):
    rv = await server.get("/core4/api/v1/_info?search=!&per_page=1000")
    assert rv.code == 200
    return [i for i in rv.json()["data"] if i[key] and qn in i[key]]


async def test_info_listing(info_server):
    await info_server.login()
    handler = await get_info(info_server, 'tests.api.test_info.LinkHandler1')
    assert len(handler) == 4
    enter = [i["enter_url"] for i in handler]
    assert "http://uni-m.de" in enter
    assert "http://uni-xxx.de" in enter
    assert "http://www.google.de" in enter


async def test_static_info(info_server):
    await info_server.login()
    handler = await get_info(info_server, 'static info', key="title")
    assert len(handler) == 1
    rscid = handler[0]["rsc_id"]
    url = "/test/_info/card/" + rscid
    rv = await info_server.get(url)
    assert rv.ok
    css = "/test/_asset/default/" + rscid + "/bootstrap-material-design.custom.css"
    assert css in rv.body.decode("utf-8")
    pprint(rv.body)
    rv = await info_server.get(css)
    assert rv.ok

    url = "/test/_info/help/" + rscid
    rv = await info_server.get(url)
    # print(rv.body)
    assert rv.ok


async def test_link_info(info_server):
    await info_server.login()
    handler = await get_info(info_server, 'goto google', key="title")
    assert len(handler) == 1
    rscid = handler[0]["rsc_id"]
    url = "/test/_info/card/" + rscid
    rv = await info_server.get(url)
    assert rv.ok
    css = "/test/_asset/default/" + rscid + "/bootstrap-material-design.custom.css"
    assert css in rv.body.decode("utf-8")
    pprint(rv.body)
    rv = await info_server.get(css)
    assert rv.ok

    url = "/test/_info/help/" + rscid
    rv = await info_server.get(url)
    assert rv.ok

    url = "/test/_info/enter/" + rscid
    rv = await info_server.get(url)
    assert rv.code == 405  # todo: requires improvement == redirect

async def test_version_info(info_server):
    await info_server.login()
    rv1 = await info_server.get("/core4/api/v1/_info")
    assert rv1.code == 200
    ep = rv1.json()["data"]
    t = 'core4.api.v1.request.standard.login.LoginHandler'
    v = [i for i in ep if i["qual_name"] == t][0]
    assert v["version"] == core4.__version__