import os

import pymongo
import pytest
from threading import Thread

import core4.service.setup
import core4.util.data
import core4.util.tool
from core4.api.v1.test import ClientServer
from example.voting.server import VotingApp

MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'voting_test'


@pytest.fixture(autouse=True)
def setup(tmpdir):
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"
    os.environ["CORE4_OPTION_api__setting__debug"] = "!!bool True"
    os.environ["CORE4_OPTION_api__setting__cookie_secret"] = "blabla"
    os.environ[
        "CORE4_OPTION_example__DEFAULT__mongo_database"] = MONGO_DATABASE
    conn = pymongo.MongoClient(MONGO_URL)
    conn.drop_database(MONGO_DATABASE)
    core4.logger.mixin.logon()
    yield
    # conn.drop_database(MONGO_DATABASE)
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    core4.util.tool.Singleton._instances = {}
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


@pytest.fixture()
def http():
    server = ClientServer(VotingApp)
    server.token = None
    yield server
    server.stop()


def test_init(http):
    rv = http.get("/profile")
    assert rv.status_code == 401


def test_register(http):
    rv = http.post("/register", json={"token": "secret_token", "id": "mra"})
    assert rv.status_code == 200


def test_create_session(http):
    rv = http.post("/session", json={"token": "secret_token",
                                     "data": {"label": "Feeling"}})
    assert rv.status_code == 400
    assert "Missing argument question" in rv.json()["error"]

    rv = http.post("/session", json={"token": "secret_token",
                                     "question": "Do you feel good?",
                                     "data": "bla"})
    assert rv.status_code == 400
    assert "parameter [data] expected as_type [dict]" in rv.json()["error"]

    rv = http.post("/session", json={"token": "secret_token",
                                     "question": "Do you feel good?",
                                     "data": {"label": "Feeling"}})
    assert rv.status_code == 200
    rv = http.post("/session", json={"token": "secret_token",
                                     "question": "Do you feel good?",
                                     "data": {"label": "Feeling"}})
    assert rv.status_code == 200


def test_session_listing(http):
    for i in range(1, 5):
        rv = http.post("/session", json={
            "token": "secret_token",
            "question": "Do you like number %d?" % (i),
            "data": {"label": "Number %d" % (i)}})
        assert rv.status_code == 200
    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200
    assert 4 == len(rv.json()["data"])


def helper_session_0(http):
    test_session_listing(http)
    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200
    session = rv.json()["data"][0]
    rv = http.get("/session/" + session["session_id"],
                  json={"token": "secret_token"})
    assert rv.status_code == 200
    data = rv.json()["data"]
    return data


def test_session_detail(http):
    data = helper_session_0(http)
    data.pop("created_at")
    assert data == {
        'session_id': data["session_id"],
        'question': 'Do you like number 1?',
        'data': {
            'label': 'Number 1'
        },
        'state': 'CLOSED'
    }


def test_open_session(http):
    data = helper_session_0(http)
    rv = http.post("/start/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200
    rv = http.get("/session/" + data["session_id"],
                  json={"token": "secret_token"})
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["state"] == "OPEN"

    rv = http.post("/start/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session/" + data["session_id"],
                  json={"token": "secret_token"})
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["state"] == "OPEN"
    return data


def test_open_session_url_param(http):
    data = helper_session_0(http)
    rv = http.post("/start/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200
    rv = http.get("/session/" + data["session_id"] + "?token=secret_token")
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["state"] == "OPEN"

    rv = http.post("/start/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session/" + data["session_id"] + "?token=secret_token")
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["state"] == "OPEN"
    return data


def test_unknown_session(http):
    sid = "5be9e1e7de8b6958c33b8e1f"
    rv = http.post("/start/" + sid,
                   json={"token": "secret_token"})
    assert rv.status_code == 404
    rv = http.get("/session/" + sid,
                  json={"token": "secret_token"})
    assert rv.status_code == 404


def test_close_session(http):
    data = test_open_session(http)
    rv = http.post("/start/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.post("/stop/" + data["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session/" + data["session_id"],
                  json={"token": "secret_token"})
    assert rv.status_code == 200
    data = rv.json()["data"]
    assert data["state"] == "CLOSED"


def test_4_session(http):
    test_session_listing(http)
    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200
    data = rv.json()["data"]
    return data


def test_open_other(http):
    data = test_4_session(http)

    rv = http.post("/start/" + data[0]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200
    assert (['OPEN', 'CLOSED', 'CLOSED', 'CLOSED']
            == [i["state"] for i in rv.json()["data"]])

    rv = http.post("/start/" + data[2]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200
    assert (['CLOSED', 'CLOSED', 'OPEN', 'CLOSED']
            == [i["state"] for i in rv.json()["data"]])


def test_event(http):
    data = test_4_session(http)

    rv = http.post("/start/" + data[0]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.get("/session", json={"token": "secret_token"})
    assert rv.status_code == 200

    for i in range(10):
        rv = http.post(
            "/event",
            json={"token": "secret_token", "id": "user-%d" % (i + 1)})
        assert rv.status_code == 201

    for i in range(10):
        rv = http.post(
            "/event",
            json={"token": "secret_token", "id": "user-%d" % (i + 1)})
        assert rv.status_code == 200

    rv = http.post(
        "/event", json={"token": "secret_token", "id": "user-99"})
    assert rv.status_code == 201

    rv = http.post(
        "/event", json={"token": "secret_token", "id": "user-99"})
    assert rv.status_code == 200

    rv = http.post("/stop/" + data[0]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    rv = http.post(
        "/event", json={"token": "secret_token", "id": "user-99"})
    assert rv.status_code == 404


def test_polling(http):
    data = test_4_session(http)

    rv = http.post("/start/" + data[0]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    def make_events():
        for i in range(50):
            rv = http.post(
                "/event",
                json={"token": "secret_token", "id": "user-%d" % (i + 1)})
            assert rv.status_code == 201
        rv = http.post("/stop/" + data[0]["session_id"],
                       json={"token": "secret_token"})
        assert rv.status_code == 200

    t = Thread(target=make_events)
    t.start()
    rv = http.get("/poll/" + data[0]["session_id"],
                  json={"token": "secret_token"}, stream=True)
    ret = []
    for line in rv.iter_lines():
        if line:
            ret.append(core4.util.data.json_decode(line.decode("utf-8")))
    t.join()
    n = [i["n"] for i in ret]
    assert n == sorted(n)
    s = [i["state"] for i in ret]
    assert set(s[:-1]) == {"OPEN"}
    assert s[-1] == "CLOSED"
    rv = http.get("/poll/" + data[0]["session_id"],
                  json={"token": "secret_token"}, stream=True)
    data = rv.json()
    data.pop("timestamp")
    assert data == {'state': 'CLOSED', 'n': 50}


def test_poll_404(http):
    rv = http.post("/start/5bea5366de8b694c0389ea79",
                   json={"token": "secret_token"})
    assert rv.status_code == 404


def test_upload(http):
    source = os.path.join(os.path.dirname(__file__), "asset/sample.csv")
    files = {'file': open(source, 'rb')}
    rv = http.post("/csv?token=secret_token", files=files)
    assert rv.json()["data"] == "read dataframe in shape (10, 4)"
    assert rv.status_code == 200


def test_result(http):
    test_upload(http)

    data = test_4_session(http)

    rv = http.post("/start/" + data[0]["session_id"],
                   json={"token": "secret_token"})
    assert rv.status_code == 200

    def make_events():
        for i in range(12):
            rv = http.post(
                "/event",
                json={"token": "secret_token", "id": "user-%d" % (i + 1)})
            assert rv.status_code == 201
        rv = http.post("/stop/" + data[0]["session_id"],
                       json={"token": "secret_token"})
        assert rv.status_code == 200

    make_events()
    rv = http.post("/result", json={"token": "secret_token"})
    assert rv.status_code == 200
    from pprint import pprint
    pprint(rv.json()["data"])

