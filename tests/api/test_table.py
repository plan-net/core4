import pytest
from tests.api.test_test import setup, run, mongodb
from core4.api.v1.server import CoreApiServer, CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.tool.datatable import CoreDataTable, convert
import datetime
import random
from pprint import pprint


_ = setup
_ = mongodb


COLS = [
    {
        "name": "_id",
        "label": None,
        "key": True,
        "hide": True,
        "sortable": False,
        "click": None,
        "align": None,
        "format": "{}",
        "editable": False
    },
    {
        "name": "idx",
        "label": "#",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": True,
        "align": "left",
        "format": "{:05d}",
        "editable": True
    },
    {
        "name": "segment",
        "label": "Segment",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "left",
        "format": "{:s}",
        "editable": True
    },
    {
        "name": "real",
        "label": "Realzahl",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "left",
        "format": "{:+1.3f}",
        "editable": True
    },
    {
        "name": "value",
        "label": "Ganzzahl",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "right",
        "format": "{:d}",
        "editable": True
    },
    {
        "name": "timestamp",
        "label": "Zeitstempel",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "center",
        "format": "{:%Y-%m-%d ... %H:%M:%S}",
        "editable": True
    }
]


class TableHandler(CoreRequestHandler):
    author = "mra"
    title = "CoreDataTable example"

    async def _length(self, filter):
        return await self.collection.count_documents(filter)

    async def _query(self, skip, limit, filter, sort_by):
        return await self.collection.find(filter).sort(
            sort_by).skip(skip).limit(limit).to_list(limit)

    def initialize_request(self, *args, **kwargs):
        self.collection = self.config.tests.data1_collection
        args = dict(
            length=self._length,
            query=self._query,
            column=COLS,
            fixed_header=self.get_argument("fixed_header", bool, default=True),
            hide_header=self.get_argument("hide_header", bool, default=False),
            multi_sort=True,
            height=None,
            dense=self.get_argument("dense", bool, default=True),
            select=False,
            multi_select=False,
            search=True,
            per_page=self.get_argument("per_page", int, default=10),
            page=self.get_argument("page", int, default=0),
            filter=self.get_argument("filter", dict, default=None,
                                     dict_decode=convert),
            sort_by=self.get_argument("sort", list, default=None)
        )
        self.datatable = CoreDataTable(**args)

    async def post(self):
        self.reply(
            await self.datatable.post()
        )

    async def get(self):
        self.reply(
            await self.datatable.get()
        )


class TableServer(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/table", TableHandler)
    ]


@pytest.yield_fixture
def table_server():
    yield from run(
        CoreApiServer,
        TableServer
    )


def _make_data(coll, count=60):
    segment = ["segment A", "segment B", "segment C", "segment D",
               "segment E"]
    coll.delete_many({})
    print(coll)
    t0 = datetime.datetime(2014, 1, 1)
    for i in range(count):
        t0 += datetime.timedelta(hours=4)
        coll.insert_one({
            "timestamp": t0,
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return coll

@pytest.yield_fixture
def make_data(mongodb, count=60):
    _make_data(mongodb.data1, count)


async def test_login(table_server):
    await table_server.login()
    resp = await table_server.get('/core4/api/v1/profile')
    assert resp.code == 200


async def test_page(table_server, make_data):
    await table_server.login()

    resp = await table_server.get('/test/table')
    assert resp.code == 200
    page = resp.json()["data"]["paging"]
    assert page["page_count"] == 6
    assert page["per_page"] == 10
    assert page["total_count"] == 60
    assert page["count"] == 10

    pprint(resp.json())

    resp = await table_server.get('/test/table?per_page=25&page=2')
    assert resp.code == 200
    page = resp.json()["data"]["paging"]
    assert page["page_count"] == 3
    assert page["per_page"] == 25
    assert page["total_count"] == 60
    assert page["count"] == 10
    sorting = resp.json()["data"]["sort"]
    assert sorting == [{'ascending': True, 'name': '_id'}]

    pprint(resp.json())

    # sorting
    resp = await table_server.get('/test/table?sort=[{"name": "real", "ascending": true}]')
    assert resp.code == 200
    data = [float(i["real"]) for i in resp.json()["data"]["body"]]
    assert data == sorted(data)

    pprint(resp.json())

    # multi-sorting
    resp = await table_server.get('/test/table?per_page=60&sort=[{"name": "segment", "ascending": false}, {"name": "real", "ascending": true}]')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = [i["segment"] for i in body]
    assert data == sorted(data, reverse=True)
    for i in set(data):
        test = [float(j["real"]) for j in body if j["segment"] == i]
        assert test == sorted(test)

    pprint(resp.json())

    # filtering
    resp = await table_server.get('/test/table?per_page=60&filter={"segment": "segment D"}')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = set([i["segment"] for i in body])
    assert data == {"segment D"}

    pprint(resp.json())

    # prepare filtering with datetime
    resp = await table_server.get('/test/table?per_page=1000&sort=[{"name": "timestamp", "ascending": false}]')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = [i["timestamp"] for i in body]
    print(data)
    data = [datetime.datetime.strptime(i["timestamp"], "%Y-%m-%d ... %H:%M:%S") for i in body]
    assert data == sorted(data, reverse=True)
    middle = data[30]

    pprint(resp.json())

    # do filtering with datetime
    resp = await table_server.get('/test/table?per_page=1000&filter={"timestamp": {"$gte": {"$datetime": "' + middle.isoformat() + '"}}}')
    assert resp.code == 200
    page = resp.json()["data"]["paging"]
    assert page["page_count"] == 1
    assert page["per_page"] == 1000
    assert page["total_count"] == 31
    assert page["count"] == 31

    body = resp.json()["data"]["body"]
    data = [datetime.datetime.strptime(i["timestamp"], "%Y-%m-%d ... %H:%M:%S") for i in body]
    assert 31 == sum([1 for i in data if i >= middle])


if __name__ == '__main__':
    from core4.api.v1.tool.functool import serve
    from core4.base.main import CoreBase
    class T(CoreBase):
        def get_db(self):
            return self.config.tests.data1_collection
    _make_data(T().get_db())
    serve(TableServer)
