from pprint import pprint

from tests.api.test_job import worker
from tests.api.test_test import setup, mongodb, core4api

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

    # resp = await core4api.put(
    #     '/core4/api/v1/store')
    # assert resp.code == 200
    # data = resp.json()["data"]
    # pprint(data)
    # assert data == {'doc': {'_id': '/default/lufthansa/eurowings/team-a',
    #                         'hallo': 'Europa',
    #                         'hello': None,
    #                         'kranich': True,
    #                         'team': True},
    #                 'parents': ['/',
    #                             '/default',
    #                             '/default/lufthansa',
    #                             '/default/lufthansa/eurowings',
    #                             '/default/lufthansa/eurowings/team-a']}

    resp = await core4api.delete('/core4/api/v1/store/default/lufthansa')
    assert resp.code == 400

    # for doc in ['/default/lufthansa/eurowings/team-a',
    #             '/default/lufthansa/eurowings',
    #             '/default/lufthansa/air-berlin',
    #             '/default/lufthansa']:
    #     resp = await core4api.put('/core4/api/v1/store' + doc)
    #     assert resp.code == 200

    resp = await core4api.delete(
        '/core4/api/v1/store/default/lufthansa?recursive=1')
    assert resp.code == 200

    # for doc in ['/default/lufthansa/eurowings/team-a',
    #             '/default/lufthansa/eurowings',
    #             '/default/lufthansa/air-berlin',
    #             '/default/lufthansa']:
    #     resp = await core4api.put('/core4/api/v1/store' + doc)
    #     assert resp.code == 404

    # resp = await core4api.put('/core4/api/v1/store')
    # assert resp.code == 200

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
    assert resp.json()["data"] == {
        'doc': {'_id': '/outlier', 'hello': 'root', 'out': True},
        'parents': ['/', '/outlier']}

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

    assert resp.json()["data"] == {'doc': {'_id': '/', 'hello': 'root'},
                                   'parents': ['/']}

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