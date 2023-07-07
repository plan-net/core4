import json
import random

import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.server import CoreApiServer
from core4.util.pager import CorePager
from tests.api.test_test import setup, mongodb, run

_ = setup
_ = mongodb


@pytest.fixture()
def data(mongodb):
    coll = mongodb.data1
    segment = ["segment A", "segment B", "segement C", "segment D",
               "segment E"]
    for i in range(60):
        coll.insert_one({
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return coll


@pytest.fixture()
def page_server():
    yield from run(
        PageServer,
        CoreApiServer
    )


class PagingHandler(CoreRequestHandler):

    async def get(self):
        coll = self.config.tests.data1_collection

        async def _length(filter):
            return await coll.count_documents(filter)
            return df.shape[0]

        async def _query(skip, limit, filter, sort_by):
            return await coll.find(filter).sort(sort_by).skip(skip).limit(
                limit).to_list(limit)

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        sort_by = self.get_argument("sort", default=[('idx', -1)])
        filter = self.get_argument("filter", as_type=dict, default={})

        pager = CorePager(per_page=per_page, current_page=current_page,
                          length=_length, query=_query, sort_by=sort_by,
                          filter=filter)
        self.reply(await pager.page())


class PageServer(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/pager", PagingHandler)
    ]


async def test_simple(page_server, data):
    await page_server.login()
    assert data.count_documents({}) == 60


async def test_paging(page_server, data):
    await page_server.login()
    rv = await page_server.get("/test/pager")
    assert rv.code == 200
    print(rv.json())
    assert rv.json()["total_count"] == 60
    assert rv.json()["page_count"] == 6
    assert rv.json()["page"] == 0
    assert rv.json()["per_page"] == 10
    assert rv.json()["count"] == 10
    data = [d["idx"] for d in rv.json()["data"]]
    assert data == list(range(60, 50, -1))
    for i in range(6):
        rv = await page_server.get("/test/pager?per_page=11&page=%d" % i)
        assert rv.code == 200
        data = [d["idx"] for d in rv.json()["data"]]
        start = 60 - i * 11
        end = start - 11
        if end < 0:
            end = 0
        assert data == list(range(start, end, -1))


async def test_filtering(page_server, data):
    await page_server.login()
    filter = {"idx": {"$lte": 30}}
    url = "/test/pager?sort={}&filter={}&page=%d".format(
        json.dumps([("idx", 1)]), json.dumps(filter))

    for i in range(3):
        rv = await page_server.get(url % (i))
        assert rv.code == 200
        data = [d["idx"] for d in rv.json()["data"]]
        assert rv.json()["page_count"] == 3
        s = 1 + i * 10
        e = s + 10
        print(s, e)
        assert sorted(data) == list(range(s, e))


async def test_empty(page_server, data):
    await page_server.login()
    filter = {"idx": {"$gte": 1000}}
    url = "/test/pager?sort={}&filter={}&page=0".format(
        json.dumps([("idx", 1)]), json.dumps(filter))
    rv = await page_server.get(url)
    assert rv.code == 200
    assert rv.json()["page_count"] == 0
    assert rv.json()["data"] == []
