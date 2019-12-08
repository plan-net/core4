import datetime
import random
from pprint import pprint
import copy
import pandas as pd
import pytest
import re
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.server import CoreApiServer, CoreApiContainer
from core4.api.v1.tool.datatable import CoreDataTable, convert, CoreDataTableRequest
from tests.api.test_test import setup, run, mongodb
import json
import io

_ = setup
_ = mongodb

COLS = [
    {
        "name": "_id",
        "label": None,
        "key": True,
        "hide": True,
        "sortable": False,
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

    def mktable(self, *args, **kwargs):
        self.collection = self.config.tests.data1_collection
        args = dict(
            length=self._length,
            query=self._query,
            column=COLS,
            fixed_header=self.get_argument("fixed_header", bool, default=True),
            hide_header=self.get_argument("hide_header", bool, default=False),
            height=None,
            dense=self.get_argument("dense", bool, default=True),  # cache
            search=True,
            per_page=self.get_argument("per_page", int, default=10),  # cache
            page=self.get_argument("page", int, default=0),  # cache
            filter=self.get_argument("filter", dict, default=None,
                                     dict_decode=convert),
            sort_by=self.get_argument("sort", list, default=None)  # cache
        )
        return CoreDataTable(**args)

    async def post(self):
        datatable = self.mktable()
        self.reply(
            await datatable.post()
        )

    async def get(self):
        datatable = self.mktable()
        self.reply(
            await datatable.get()
        )


class TableHandler2(TableHandler):
    author = "mra"
    title = "CoreDataTable example 2"

    def mktable(self, *args, **kwargs):
        self.collection = self.config.tests.data1_collection
        COLS1 = copy.deepcopy(COLS)
        COLS1[-1]["format"] = lambda dt: ">>>" + str(dt)
        args = dict(
            length=self._length,
            query=self._query,
            column=COLS1,
            fixed_header=self.get_argument("fixed_header", bool, default=True),
            hide_header=self.get_argument("hide_header", bool, default=False),
            height=None,
            dense=self.get_argument("dense", bool, default=True),
            search=True,
            per_page=self.get_argument("per_page", int, default=10),
            page=self.get_argument("page", int, default=0),
            filter=self.get_argument("filter", dict, default=None,
                                     dict_decode=convert),
            sort_by=self.get_argument("sort", list, default=None)
        )
        return CoreDataTable(**args)

COLS1 = copy.deepcopy(COLS)
COLS1[-1]["format"] = lambda dt: ">>>" + str(dt)


class TableHandler3(CoreDataTableRequest):

    author = "mra"
    title = "CoreDataTable mixin example"
    column = COLS1

    async def length(self, filter):
        collection = self.config.tests.data1_collection
        return await collection.count_documents(filter)

    async def query(self, skip, limit, filter, sort_by):
        collection = self.config.tests.data1_collection
        return await collection.find(
            filter).sort(sort_by).skip(skip).limit(limit).to_list(limit)

class TableHandler4(CoreDataTableRequest):

    author = "mra"
    title = "CoreDataTable example 4"
    column = COLS

    def _build_query(self, filter):
        filter = self.convert_filter(filter)
        if filter is None:
            return {}
        if isinstance(filter, str):
            return {"search": re.compile(filter, re.I)}
        return filter

    async def length(self, filter):
        collection = self.config.tests.data1_collection
        return await collection.count_documents(self._build_query(filter))

    async def query(self, skip, limit, filter, sort_by):
        collection = self.config.tests.data1_collection
        return await collection.find(self.convert_filter(
            self._build_query(filter))).sort(sort_by).skip(skip).limit(
            limit).to_list(limit)



class TableServer(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/table", TableHandler),
        (r"/table2", TableHandler2),
        (r"/table3", TableHandler3),
        (r"/table4", TableHandler4),
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
    t0 = datetime.datetime(2014, 1, 1)
    for i in range(count):
        t0 += datetime.timedelta(hours=4)
        doc = {
            "timestamp": t0,
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        }
        doc["search"] = "".join((str(i) for i in doc.values()))
        coll.insert_one(doc)
    return coll


@pytest.yield_fixture
def make_data(mongodb, count=60):
    _make_data(mongodb.data1, count)

@pytest.yield_fixture
def make_big_data(mongodb):
    _make_data(mongodb.data1, 20000)


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
    resp = await table_server.get(
        '/test/table?sort=[{"name": "real", "ascending": true}]')
    assert resp.code == 200
    data = [float(i["real"]) for i in resp.json()["data"]["body"]]
    assert data == sorted(data)

    pprint(resp.json())

    # multi-sorting
    resp = await table_server.get(
        '/test/table?per_page=60&sort=[{"name": "segment", "ascending": false}, {"name": "real", "ascending": true}]')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = [i["segment"] for i in body]
    assert data == sorted(data, reverse=True)
    for i in set(data):
        test = [float(j["real"]) for j in body if j["segment"] == i]
        assert test == sorted(test)

    pprint(resp.json())

    # filtering
    resp = await table_server.get(
        '/test/table?per_page=60&filter={"segment": "segment D"}')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = set([i["segment"] for i in body])
    assert data == {"segment D"}

    pprint(resp.json())

    # prepare filtering with datetime
    resp = await table_server.get(
        '/test/table?per_page=1000&sort=[{"name": "timestamp", "ascending": false}]')
    assert resp.code == 200
    body = resp.json()["data"]["body"]
    data = [i["timestamp"] for i in body]
    print(data)
    data = [datetime.datetime.strptime(i["timestamp"], "%Y-%m-%d ... %H:%M:%S")
            for i in body]
    assert data == sorted(data, reverse=True)
    middle = data[30]

    pprint(resp.json())

    # do filtering with datetime
    resp = await table_server.get(
        '/test/table?per_page=1000&filter={"timestamp": {"$gte": {"$datetime": "' + middle.isoformat() + '"}}}')
    assert resp.code == 200
    page = resp.json()["data"]["paging"]
    assert page["page_count"] == 1
    assert page["per_page"] == 1000
    assert page["total_count"] == 31
    assert page["count"] == 31

    body = resp.json()["data"]["body"]
    data = [datetime.datetime.strptime(i["timestamp"], "%Y-%m-%d ... %H:%M:%S")
            for i in body]
    assert 31 == sum([1 for i in data if i >= middle])


async def test_parameter(table_server, make_data):
    await table_server.login()
    rv = await table_server.post("/test/table", json={"per_page": 5})
    pprint(rv.json())
    paging = rv.json()["data"]["paging"]
    assert 5 == paging["per_page"]


async def test_lambda(table_server, make_data):
    await table_server.login()
    rv = await table_server.post("/test/table2", json={"per_page": 5})
    pprint(rv.json())
    paging = rv.json()["data"]["paging"]
    assert 5 == paging["per_page"]
    pprint(rv.json())


async def test_sort(table_server, make_data):
    await table_server.login()
    rv = await table_server.get("/test/table")
    data = [i["_id"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data)
    assert len(data) == 10
    pprint(rv.json()["data"]["sort"])
    cols = [{"name": i["name"], "align": i["align"], "hide": i["hide"]} for i in
            rv.json()["data"]["column"]]
    pprint(cols)
    cols = [
        {'align': 'left', 'hide': False, 'name': 'segment'},
        {'align': 'right', 'hide': False, 'name': 'value'},
        {'align': 'left', 'hide': True, 'name': 'idx'},
        {'align': 'left', 'hide': True, 'name': 'real'},
        {'align': 'center', 'hide': True, 'name': 'timestamp'}
    ]
    print("CHANGE")
    rv = await table_server.post("/test/table", json={"sort": [
        {"name": "idx", "ascending": False}
    ], "per_page": 32, "column": cols})
    assert rv.code == 200
    data = [i["idx"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data, reverse=True)
    assert len(data) == 32
    pprint(rv.json()["data"]["sort"])

    cols = [{"name": i["name"], "align": i["align"], "hide": i["hide"]} for i in
            rv.json()["data"]["column"]]
    pprint(cols)
    pprint(rv.json()["data"]["column"])

    df = pd.DataFrame(rv.json()["data"]["body"])
    print(df.to_string())
    # access stored settings with GET

    rv = await table_server.get("/test/table")
    assert rv.code == 200

    data = [i["_id"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data)

    data = [i["idx"] for i in rv.json()["data"]["body"]]
    # assert data == sorted(data, reverse=True)

    assert len(data) == 10

async def test_persist(table_server, make_data):
    await table_server.login()
    rv = await table_server.get("/test/table3")
    data = [i["_id"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data)
    assert len(data) == 10
    # pprint(rv.json()["data"]["sort"])
    cols = [{"name": i["name"], "align": i["align"], "hide": i["hide"]} for i in
            rv.json()["data"]["column"]]
    # pprint(cols)
    cols = [
        {'align': 'left', 'hide': False, 'name': 'segment'},
        {'align': 'right', 'hide': False, 'name': 'value'},
        {'align': 'left', 'hide': True, 'name': 'idx'},
        {'align': 'left', 'hide': True, 'name': 'real'},
        {'align': 'center', 'hide': True, 'name': 'timestamp'}
    ]
    rv = await table_server.post("/test/table3", json={"sort": [
        {"name": "idx", "ascending": False}
    ], "per_page": 32, "column": cols})
    assert rv.code == 200
    data = [i["idx"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data, reverse=True)
    assert len(data) == 32
    # pprint(rv.json()["data"]["sort"])

    cols = [{"name": i["name"], "align": i["align"], "hide": i["hide"]} for i in
            rv.json()["data"]["column"]]
    pprint(cols)
    pprint(rv.json()["data"]["column"])

    df = pd.DataFrame(rv.json()["data"]["body"])
    # print(df.to_string())
    # access stored settings with GET

    rv = await table_server.get("/test/table3")
    assert rv.code == 200
    paging = rv.json()["data"]["paging"]
    pprint(paging)

    # data = [i["_id"] for i in rv.json()["data"]["body"]]
    # assert data == sorted(data)

    data = [i["idx"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data, reverse=True)

    assert len(data) == 32

    rv = await table_server.post("/test/table3", json={"sort": [
        {"name": "segment", "ascending": True}
    ]})
    assert rv.code == 200
    data = [i["segment"] for i in rv.json()["data"]["body"]]
    assert data == sorted(data, reverse=False)

    cols = [
        {'align': 'left', 'hide': False, 'name': 'segment'},
        {'align': 'right', 'hide': False, 'name': 'value'}
    ]
    rv = await table_server.post("/test/table3", json={"sort": [
        {"name": "idx", "ascending": False}
    ], "per_page": 32, "column": cols})
    assert rv.code == 200

    rv = await table_server.post("/test/table3", json={"reset": True})
    assert rv.code == 200
    paging = rv.json()["data"]["paging"]
    pprint(paging)
    assert paging["per_page"] == 10

async def test_filter(table_server, make_data):
    await table_server.login()

    rv = await table_server.get("/test/table4?filter=A")
    assert rv.code == 200
    print(rv.json()["data"]["paging"]["total_count"])
    ret = [i["segment"] for i in rv.json()["data"]["body"]]
    assert set(ret) == {"segment A"}

    rv = await table_server.post("/test/table4",
                                 json={"filter": '{"real": {"$gte": 50}}'})
    assert rv.code == 200
    ret = [1 for i in rv.json()["data"]["body"] if float(i["real"]) < 50.]
    assert ret == []

async def test_big_download(table_server, make_big_data):
    await table_server.login()

    rv = await table_server.get('/test/table4?download=1&sort=[{"name": "value", "ascending": false},{"name": "real", "ascending": false}]')
    assert rv.code == 200
    print(len(rv.body))

async def test_download(table_server, make_data):
    await table_server.login()

    column = [
        ("segment", True),
        ("value", True),
        ("_id", False),
        ("idx", False),
        ("real", False),
        ("timestamp", False)]
    rv = await table_server.post('/test/table4?column=' + json.dumps(
        [{"name": i[0], "hide": not i[1]} for i in column]))
    assert rv.code == 200
    column = [i["name"] for i in rv.json()["data"]["column"] if not i["hide"]]
    assert column == ["segment", "value"]

    column = [
        ("value", True),
        ("segment", True),
        ("_id", False),
        ("idx", False),
        ("real", False),
        ("timestamp", False)]
    rv = await table_server.get('/test/table4?column=' + json.dumps(
        [{"name": i[0], "hide": not i[1]} for i in column]))
    assert rv.code == 200
    column = [i["name"] for i in rv.json()["data"]["column"] if not i["hide"]]
    assert column == ["value", "segment"]

    rv = await table_server.get('/test/table4')
    assert rv.code == 200
    column = [i["name"] for i in rv.json()["data"]["column"] if not i["hide"]]
    assert column == ["segment", "value"]

    column = [
        ("value", True),
        ("segment", True),
        ("_id", False),
        ("idx", True),
        ("real", False),
        ("timestamp", False)]
    rv = await table_server.get('/test/table4?download=1&column=' + json.dumps(
        [{"name": i[0], "hide": not i[1]} for i in column]))
    assert rv.code == 200
    stream = io.BytesIO(rv.body)
    df = pd.read_csv(stream)
    assert df.columns.tolist() == ["Ganzzahl", "Segment", "#"]

    rv = await table_server.get('/test/table4?download=1')
    assert rv.code == 200
    stream = io.BytesIO(rv.body)
    df = pd.read_csv(stream)
    assert df.columns.tolist() == ["Segment", "Ganzzahl"]

    rv = await table_server.get('/test/table4?download=1&reset=1')
    assert rv.code == 200
    stream = io.BytesIO(rv.body)
    df = pd.read_csv(stream)
    assert df.columns.tolist() == ["#", "Segment", "Realzahl", "Ganzzahl",
                                   "Zeitstempel"]

    rv = await table_server.get('/test/table4?download=1')
    assert rv.code == 200
    stream = io.BytesIO(rv.body)
    df = pd.read_csv(stream)
    assert df.columns.tolist() == ["Segment", "Ganzzahl"]


if __name__ == '__main__':
    from core4.api.v1.tool.functool import serve
    from core4.base.main import CoreBase


    class T(CoreBase):
        def get_db(self):
            return self.config.tests.data1_collection


    #_make_data(T().get_db(), 20000)
    serve(TableServer)

# todo: what if there are more columns specified than observed?