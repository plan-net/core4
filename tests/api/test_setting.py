import os

import pytest

from tests.api.test_test import setup, mongodb, core4api

_ = setup
_ = mongodb
_ = core4api

import random


@pytest.fixture(autouse=True)
def add_setup(tmpdir):
    os.environ["CORE4_OPTION_user_setting___general__language"] = "FR"


async def test_general_url_restriction(core4api):
    await core4api.login()
    data = {"data": {"_general": {"language": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting", json=data)
    assert response.code == 200
    assert response.json()["data"]["_general"]["language"] == "UA"

    response = await core4api.get("/core4/api/v1/setting/_general//language")
    assert response.code == 400


async def test_response_contains_data(core4api):
    await core4api.login()
    to_send = {"_general": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok
    assert response.json()["data"] == to_send


async def test_levels_restrictions(core4api):
    await core4api.login()
    # empty key in level1
    to_send = {"": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.code == 400

    # empty key in level2
    to_send = {"_general": {"": {"code": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.code == 400

    # empty key in level2
    to_send = {"": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting/_general",
                                   json={"data": to_send})
    assert response.code == 400

    # invalid level1 structure
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": 123})
    assert response.code == 400

    # invalid level2 structure
    response = await core4api.post("/core4/api/v1/setting/_general",
                                   json={"data": 123})
    assert response.code == 400

    # invalid system key on level1, names with underscore reserved
    to_send = {"_project": {"language": {"code": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.code == 400

    # invalid system key on level1, names with underscore reserved
    to_send = {"language": {"code": "UA"}}
    response = await core4api.post("/core4/api/v1/setting/_project",
                                   json={"data": to_send})
    assert response.code == 400

    # empty resource in url
    to_send = {"code": "UA"}
    response = await core4api.post("/core4/api/v1/setting//language",
                                   json={"data": to_send})
    assert response.code == 400


async def test_get_default_setting(core4api):
    await core4api.login()
    response = await core4api.get("/core4/api/v1/setting")
    assert response.ok

    general_ = response.json()["data"]["_general"]
    assert type(general_) is dict
    assert general_["language"] == "FR"


async def test_default_settings_override(core4api):
    await core4api.login()
    to_send = {"_general": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    expect = {
        "_general": {
            "language": "UA",
            'contact': 'mail@mailer.com',
            'menu': [
                {'About': '/about'},
                {'Profile': '/core4/api/v1/profile'}
            ]
        }
    }
    print(response.json()["data"])
    assert response.json()["data"] == expect


async def test_delete_settings(core4api):
    await core4api.login()
    to_send = {"_general": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    expect = {
        "_general": {
            "language": "UA",
            'contact': 'mail@mailer.com',
            'menu': [
                {'About': '/about'},
                {'Profile': '/core4/api/v1/profile'}
            ]
        }
    }
    assert response.json()["data"] == expect

    response = await core4api.delete("/core4/api/v1/setting")
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    assert response.ok
    assert response.json()["data"]["_general"]["language"] == "FR"


async def test_delete_nested_settings(core4api):
    await core4api.login()
    to_send = {"project": {"setting1": 57, "setting2": 111}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    assert response.json()["data"] == {"_general": {
        "language": "FR",
        'contact': 'mail@mailer.com',
        'menu': [
            {'About': '/about'},
            {'Profile': '/core4/api/v1/profile'}
        ]},
        "project": {"setting1": 57,
                    "setting2": 111}}
    response = await core4api.delete("/core4/api/v1/setting/project/setting1")
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    assert response.ok
    assert response.json()["data"] == {
        "_general": {
            "language": "FR",
            'contact': 'mail@mailer.com',
            'menu': [
                {'About': '/about'},
                {'Profile': '/core4/api/v1/profile'}
            ]
        },
        "project": {"setting2": 111}}

    response = await core4api.delete("/core4/api/v1/setting/project")
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    assert response.ok
    assert response.json()["data"] == {
        "_general": {
            "language": "FR",
            'contact': 'mail@mailer.com',
            'menu': [
                {'About': '/about'},
                {'Profile': '/core4/api/v1/profile'}
            ]
        }
    }


async def test_user_override(core4api):
    await core4api.login()
    response = await core4api.post("/core4/api/v1/roles", json=dict(
        name="test",
        realname="test user",
        passwd="password",
        email="test@user.com",
        perm=["api://core4.api.v1"]
    ))

    assert response.ok
    test_data = {"random": random.randint(0, 42)}
    response = await core4api.post(
        "/core4/api/v1/setting/test_project/test_setting?username=test",
        json={"data": test_data})
    assert response.ok

    await core4api.login("test", "password")

    response = await core4api.get(
        "/core4/api/v1/setting/test_project/test_setting")
    assert response.ok
    assert response.json()["data"] == test_data


async def test_set_system_setting(core4api):
    await core4api.login()
    data = {"data": 123}
    response = await core4api.post("/core4/api/v1/setting/_project",
                                   json=data)
    assert response.json()["code"] == 400

    data = {"data": 123}
    response = await core4api.post("/core4/api/v1/setting/_general",
                                   json=data)
    assert response.json()["code"] == 400

    data = {"data": {"_general": 123}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json=data)
    assert response.json()["code"] == 400

    data = {"data": {"_other": 123}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json=data)
    assert response.json()["code"] == 400

    data = {"data": {"_general": {"language": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json=data)
    assert response.json()["code"] == 200
    assert response.json()["data"]["_general"]["language"] == "UA"

    data = {"data": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting/_general",
                                   json=data)
    assert response.code == 200


async def test_update_settings(core4api):
    await core4api.login()
    to_send = {"_general": {"language": "UA"}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.put("/core4/api/v1/setting/_general/language",
                                  json={"data": "RU"})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting")
    assert response.ok
    assert response.json()["data"]["_general"]["language"] == "RU"


async def test_create_nested_settings(core4api):
    await core4api.login()
    to_send = {"_general": {"language": {"code": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.post("/core4/api/v1/setting/_general/language",
                                   json={"data": {"name": "Ukraine"}})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting/_general")
    assert response.ok
    assert response.json()["data"]["language"] == {"code": "UA",
                                                   "name": "Ukraine"}


async def test_empty_string_as_key(core4api):
    await core4api.login()
    to_send = {"_general": {"language": {"code": "UA"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    # after level2 no restrictions, bullshit in, bullshit out :[
    response = await core4api.post("/core4/api/v1/setting/_general/language",
                                   json={"data": {"": "Ukraine"}})
    assert response.code == 200

    response = await core4api.get("/core4/api/v1/setting/_general")
    assert response.ok
    assert response.json()["data"]["language"] == {"code": "UA", "": "Ukraine"}


async def test_get_nested_settings(core4api):
    await core4api.login()
    to_send = {"_general": {"language": {"code": "LT"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.get(
        "/core4/api/v1/setting/_general/language/code")
    assert response.ok
    assert response.json()["data"] == "LT"


async def test_update_nested_settings(core4api):
    await core4api.login()
    to_send = {"_general": {"language": {"code": "LT"}}}
    response = await core4api.post("/core4/api/v1/setting",
                                   json={"data": to_send})
    assert response.ok

    response = await core4api.post("/core4/api/v1/setting/_general/language",
                                   json={"data": {"name": "Ukraine"}})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting/_general/language")
    assert response.ok
    assert response.json()["data"] == {"code": "LT", "name": "Ukraine"}

    response = await core4api.put(
        "/core4/api/v1/setting/_general/language/code",
        json={"data": "RU"})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting/_general/language")
    assert response.ok
    assert response.json()["data"] == {"code": "RU", "name": "Ukraine"}

    response = await core4api.put(
        "/core4/api/v1/setting/_general/language/name",
        json={"data": "Russia"})
    assert response.ok

    response = await core4api.get("/core4/api/v1/setting/_general/language")
    assert response.ok
    assert response.json()["data"] == {"code": "RU", "name": "Russia"}
