import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.server import CoreApiServer
from tests.api.test_test import setup, mongodb, run
from core4.data.table import CoreDataTable
from  core4.util.pager import CorePager

import random

_ = setup
_ = mongodb


def make_data(coll, count=60):
    segment = ["segment A", "segment B", "segment C", "segment D",
               "segment E"]
    coll.delete_many({})
    for i in range(count):
        coll.insert_one({
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return coll


@pytest.fixture()
def data(mongodb):
    coll = mongodb.data1
    make_data(coll)

@pytest.fixture()
def table_server():
    yield from run(
        TableServer1,
        CoreApiServer
    )


class SimpleHandler(CoreRequestHandler):

    async def get(self):
        self.reply("OK")


class TableHandler1(CoreRequestHandler):

    async def get(self, path):

        coll = self.config.tests.data1_collection

        async def _length(filter):
            return await coll.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            return await coll.find(filter).sort(sort_by).skip(skip).limit(
                limit).to_list(limit)

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        sort_by = self.get_argument("sort", as_type=list, default=[['segment', 1]])
        filter = self.get_argument("filter", as_type=dict, default={})

        table = CoreDataTable(
            "table1/data",
            height="320px",
            column=[
                ("_id", True),
                ("idx", True),
                ("segment", True),
                ("real", True),
                ("value", True),
            ],
            per_page=per_page,
            current_page=current_page,
            length=_length,
            query=_query,
            sort_by=sort_by,
            filter=filter,
        )

        if path == "":
            self.render(
                "table/table1.html",
                dt=table,
            )
        elif path == "/data":
            self.reply(await table.page())


class TableServer1(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/simple", SimpleHandler),
        (r"/table1(.*)", TableHandler1),
        # (r"/data1", TableData1),
    ]


async def test_simple(table_server):
    await table_server.login()
    rv = await table_server.get("/test/simple")
    assert rv.code == 200


async def test_table1(table_server, data):
    await table_server.login()
    rv = await table_server.get("/test/table1")
    assert rv.code == 200
    open("/tmp/table1.html", "wb").write(rv.body)

if __name__ == '__main__':
    # import pymongo
    # mongo = pymongo.MongoClient("mongodb://core:654321@localhost:27017")
    # make_data(mongo.core4test.data1, 1000)

    import os
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
    from core4.api.v1.tool.functool import serve
    serve(TableServer1)