from pprint import pprint
import requests
from tests.api.test_job import worker
from tests.api.test_test import setup, mongodb, core4api
import base64

_ = setup
_ = mongodb
_ = core4api
_ = worker


async def test_create(core4api):
    await core4api.login()
    resp = await core4api.post('/core4/api/v1/store/default',
                               json={"hello": "world"})
    assert resp.code == 404

    resp = await core4api.post('/core4/api/v1/store',
                               json={"hello": "root"})
    assert resp.code == 200

    resp = await core4api.post('/core4/api/v1/store/default',
                               json={"hello": "world"})
    assert resp.code == 200

    resp = await core4api.post('/core4/api/v1/store/outlier',
                               json={"out": True})
    assert resp.code == 200

    resp = await core4api.post('/core4/api/v1/store/defaultx/abc',
                               json={})
    assert resp.code == 404

    resp = await core4api.post('/core4/api/v1/store/default/lufthansa',
                               json={"hallo": "welt", "hello": None,
                                     "kranich": True})
    assert resp.code == 200

    resp = await core4api.post(
        '/core4/api/v1/store/default/lufthansa/eurowings',
        json={"hallo": "Europa"})
    assert resp.code == 200

    resp = await core4api.post(
        '/core4/api/v1/store/default/lufthansa/air-berlin',
        json={"dead": 1.23})
    assert resp.code == 200

    resp = await core4api.post(
        '/core4/api/v1/store/default/lufthansa/eurowings/team-a',
        json={"team": True})
    assert resp.code == 200

    resp = await core4api.put(
        '/core4/api/v1/store')
    assert resp.code == 200

    resp = await core4api.delete('/core4/api/v1/store/default/lufthansa')
    assert resp.code == 400

    resp = await core4api.delete(
        '/core4/api/v1/store/default/lufthansa?recursive=1')
    assert resp.code == 200

    r1 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role 1",
        passwd="test_role1",
        email="test@mail.de",
        role=["standard_user"],
        perm=["app://store/outlier"]
    ))
    assert r1.code == 200

    await core4api.login("test_role1", "test_role1")

    resp = await core4api.put('/core4/api/v1/store')
    assert resp.code == 200

    default = {
        "contact": "mail@mailer.com",
        "profile": "/core4/api/v1/profile",
        "menu": [
            {"Contact": "mailto:mail@mailer.com?subject=core4os support request"},
            {"About": "/core4/api/v1/about"}
        ],
        "tag": [
            "app",
            "analytics",
            "data",
            "new"
        ]
    }
    for k in ("contact", "profile", "menu", "tag"):
        assert resp.json()["data"]["doc"][k] == default[k]
    assert resp.json()["data"]["doc"]["_id"] == "/outlier"
    assert resp.json()["data"]["doc"]["hello"] == "root"
    assert resp.json()["data"]["doc"]["out"] is True
    assert resp.json()["data"]["parents"] == ['/', '/outlier']

    await core4api.login()
    r2 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role2",
        realname="test role 2",
        passwd="test_role2",
        email="test1@mail.de",
        role=["standard_user"]
    ))
    assert r1.code == 200

    await core4api.login("test_role2", "test_role2")

    resp = await core4api.put('/core4/api/v1/store')
    assert resp.code == 200

    for k in ("contact", "profile", "menu", "tag"):
        assert resp.json()["data"]["doc"][k] == default[k]
    assert resp.json()["data"]["doc"]["_id"] == "/"
    assert resp.json()["data"]["doc"]["hello"] == "root"
    assert "out" not in resp.json()["data"]["doc"]

    resp = await core4api.delete('/core4/api/v1/store/default')
    assert resp.code == 403

    await core4api.login()
    resp = await core4api.delete('/core4/api/v1/store')
    assert resp.code == 400

    resp = await core4api.delete('/core4/api/v1/store/')
    assert resp.code == 400

    resp = await core4api.delete('/core4/api/v1/store/default')
    assert resp.code == 200

    resp = await core4api.delete('/core4/api/v1/store/')
    assert resp.code == 400

    resp = await core4api.delete('/core4/api/v1/store/?recursive=1')
    assert resp.code == 200
    pprint(resp.json())

async def test_skin_example(core4api):
    # create user assigned to store "app://store/lufthansa
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role",
        realname="test role",
        passwd="test_role",
        email="test@mail.de",
        role=["standard_user"],
        perm=["app://store/lufthansa"]
    ))
    assert rv.code == 200
    # create default store
    rv = await core4api.post(
        '/core4/api/v1/store', json={"primary": "red", "secondary": "blue"})
    assert rv.code == 200
    # create client store overwriting selected values
    rv = await core4api.post(
        '/core4/api/v1/store/lufthansa', json={"primary": "orange"})
    assert rv.code == 200
    # login as test user
    await core4api.login("test_role", "test_role")
    # access the store automatically routed by app://store/lufthansa key
    rv = await core4api.put('/core4/api/v1/store')
    assert rv.code == 200
    pprint(rv.json())

async def test_image_example(core4api):
    # create user assigned to store "app://store/lufthansa
    await core4api.login()
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role",
        realname="test role",
        passwd="test_role",
        email="test@mail.de",
        role=["standard_user"],
        perm=["app://store/lufthansa"]
    ))
    assert rv.code == 200
    rv = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role1",
        passwd="test_role1",
        email="test1@mail.de",
        role=["standard_user"],
        perm=[]
    ))
    assert rv.code == 200
    # create default store
    img = requests.get("https://file-examples-com.github.io/uploads/2017/10/file_example_PNG_500kB.png")
    b1 = base64.encodebytes(img.content)
    rv = await core4api.post(
        '/core4/api/v1/store', json={"primary": "red", "secondary": "blue", "logo": b1.decode("utf-8")})
    assert rv.code == 200
    # create client store overwriting selected values

    img = requests.get("https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png")
    b2 = base64.encodebytes(img.content)
    rv = await core4api.post(
        '/core4/api/v1/store/lufthansa', json={"primary": "orange", "logo": b2.decode("utf-8")})
    assert rv.code == 200
    # login as test user
    await core4api.login("test_role", "test_role")
    # access the store automatically routed by app://store/lufthansa key
    rv = await core4api.put('/core4/api/v1/store')
    assert rv.code == 200
    #pprint(rv.json())
    img = rv.json()["data"]["doc"]["logo"]
    assert img == b2.decode("utf-8")

    await core4api.login("test_role1", "test_role1")
    # access the store automatically routed by app://store/lufthansa key
    rv = await core4api.put('/core4/api/v1/store')
    assert rv.code == 200
    #pprint(rv.json())
    img = rv.json()["data"]["doc"]["logo"]
    assert img == b1.decode("utf-8")


async def test_base_store():
    from core4.api.v1.request.store import CoreStore
    from core4.api.v1.request.role.model import CoreRole
    r = await CoreRole().load_one(_id="admin")
    data = await CoreStore.load(r)
    assert data["doc"]["logout"] == "/core4/api/v1/login"
    assert data["doc"]["reset"] == "/core4/api/v1/reset"


async def test_dyn_login(core4api):
    rv = await core4api.get("/core4/api/v1/roles",
                            headers={"Accept": "text/html"})
    body = rv.body.decode("utf-8")
    assert "/core4/api/v1/reset" in body
    assert "/core4/api/v1/login" in body
    rv = await core4api.get("/core4/api/v1/roles", follow_redirects=False)
    print(dict(rv.headers))
    assert rv.code == 302
    assert rv.headers["Location"].startswith("/core4/api/v1/login?")
    assert rv.headers["Location"].endswith("/core4/api/v1/roles")


async def test_dyn_login2(core4api):
    await core4api.login()
    resp = await core4api.post('/core4/api/v1/store', json={})
    assert resp.code == 200

    resp = await core4api.post('/core4/api/v1/store/client-A',
                               json={"reset": "/core4/api/v1/logout-dummy"})
    assert resp.code == 200

    r1 = await core4api.post("/core4/api/v1/roles", body=dict(
        name="test_role1",
        realname="test role 1",
        passwd="test_role1",
        email="test@mail.de",
        role=["standard_user"],
        perm=["app://store/client-A"]
    ))
    assert r1.code == 200
    rv = await core4api.login("test_role1", "test_role1")
    print(rv)
    resp = await core4api.get('/core4/api/v1/profile')
    assert resp.code == 200
    print(resp.json())
    rv = await core4api.get("/core4/api/v1/logout",
                            headers={"Accept": "text/html"})
    body = rv.body.decode("utf-8")
    assert "<!-- LOGIN -->" in body
    assert "/core4/api/v1/logout-dummy" in body

    resp = await core4api.get('/core4/api/v1/profile')
    print(resp.json())
    assert resp.code == 200
