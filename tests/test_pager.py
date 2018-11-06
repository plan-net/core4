import pytest
from core4.api.v1.application import serve, CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.queue.job import JobHandler, JobPost


from tests.api.test_job import LocalTestServer, StopHandler, setup
import random
import pymongo
from core4.util.pager import CorePager
import pandas as pd

MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'


class SimpleHandler(CoreRequestHandler):

    def get(self):
        self.reply("OK")

def data():
    segment = ["segment A", "segment B", "segement C", "segment D",
               "segment E"]
    data = []
    for i in range(60):
        data.append({
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return pd.DataFrame(data)


class PagingHandler(CoreRequestHandler):

    async def get(self):

        df = pd.DataFrame(data())

        async def _length(filter):
            return df.shape[0]

        async def _query(skip, limit, filter, sort_by):
            if filter:
                self.logger.warning("filter not supported")
            t = df[skip:skip+limit]
            if sort_by:
                t.sort_values(
                    [sort_by[0]],
                    ascending=True if sort_by[1] == 1 else False,
                inplace=True)
            return t.to_dict("rec")

        per_page = int(self.get_argument("per_page", 10))
        current_page = int(self.get_argument("page", 0))
        sort_by = self.get_argument("sort", [])

        pager = CorePager(per_page=per_page, current_page=current_page,
                          length=_length, query=_query, sort_by=sort_by)
        self.reply(await pager.page())


class MyTestServer(LocalTestServer):
    base_url = "/core4/api/v1"

    def start(self, *args, **kwargs):
        class CoreApiTestServer(CoreApiContainer):
            rules = [
                (r'/kill', StopHandler),
                (r'/simple', SimpleHandler),
                (r'/jobs', JobHandler),
                (r'/enqueue', JobPost),
                (r'/page', PagingHandler),
            ]

        return CoreApiTestServer



@pytest.fixture(autouse=True)
def reset(mongodb):
    mongodb.drop_database(MONGO_DATABASE)

@pytest.fixture
def mongodb():
    return pymongo.MongoClient(MONGO_URL)


@pytest.fixture
def testdb(mongodb):
    return mongodb[MONGO_DATABASE]


@pytest.fixture
def data1(testdb):
    coll = testdb.data1
    segment = ["segment A", "segment B", "segement C", "segment D", "segment E"]
    for i in range(60):
        coll.insert_one({
            "idx": i+1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return coll


@pytest.fixture()
def http():
    server = MyTestServer()
    yield server
    server.stop()

def test_simple(http):
    rv = http.get("/simple")
    assert rv.status_code == 200

def test_page(http):
    rv = http.get("/page")
    assert rv.status_code == 200
    df = pd.DataFrame(rv.json()["data"])
    assert df.idx.tolist() == list(range(1, 11))

    rv = http.get("/page?page=1")
    assert rv.status_code == 200
    df = pd.DataFrame(rv.json()["data"])
    assert df.idx.tolist() == list(range(11, 21))

    rv = http.get("/page?page=0&per_page=20")
    assert rv.status_code == 200
    df = pd.DataFrame(rv.json()["data"])
    assert df.idx.tolist() == list(range(1, 21))

    rv = http.get("/page?page=1&per_page=20")
    assert rv.status_code == 200
    df = pd.DataFrame(rv.json()["data"])
    assert df.idx.tolist() == list(range(21, 41))

    rv = http.get("/page?page=2&per_page=20")
    assert rv.status_code == 200
    df = pd.DataFrame(rv.json()["data"])
    assert df.idx.tolist() == list(range(41, 61))
    assert 3 == rv.json()["page_count"]
    assert 20 == rv.json()["per_page"]
    assert 60 == rv.json()["total_count"]


def test_empty(http):
    rv = http.get("/jobs?per_page=20")
    assert rv.status_code == 200
    data = rv.json()
    assert data["count"] == 0
    assert data["data"] == []
    assert data["page"] == 0
    assert data["page_count"] == 0
    assert data["per_page"] == 20
    assert data["total_count"] == 0

def test_job_listing(http):
    for i in range(20, 1, -1):
        rv = http.post(
            "/enqueue", json=dict(name="core4.queue.helper.DummyJob",
                                  sleep=1, id=i+1))
        assert rv.status_code == 200
    rv = http.get("/jobs?per_page=6")
    assert rv.status_code == 200
    data = rv.json()
    assert data["count"] == 6
    assert data["page"] == 0
    assert data["page_count"] == 4
    assert data["per_page"] == 6
    assert data["total_count"] == 19
    orig = [d["_id"] for d in data["data"]]
    assert orig == sorted(orig)

    rv = http.get("/jobs?per_page=6&sort=args.id&order=1")
    assert rv.status_code == 200
    data = rv.json()
    assert data["count"] == 6
    assert data["page"] == 0
    assert data["page_count"] == 4
    assert data["per_page"] == 6
    assert data["total_count"] == 19
    orig = [d["args"]["id"] for d in data["data"]]
    assert orig == sorted(orig)
    orig = [d["_id"] for d in data["data"]]
    assert orig == sorted(orig, reverse=True)

    rv = http.get("/jobs?per_page=6&sort=args.id&order=-1")
    assert rv.status_code == 200
    data = rv.json()
    assert data["count"] == 6
    assert data["page"] == 0
    assert data["page_count"] == 4
    assert data["per_page"] == 6
    assert data["total_count"] == 19
    orig = [d["args"]["id"] for d in data["data"]]
    assert orig == sorted(orig, reverse=True)
    orig = [d["_id"] for d in data["data"]]
    assert orig == sorted(orig, reverse=False)

