import os
import pytest
import datetime
from random import randint

from tests.api.test_test import setup, mongodb, core4api, load_db_data

_ = setup
_ = mongodb
_ = core4api
_ = load_db_data


@pytest.fixture(autouse=True)
def add_setup(tmpdir):
    os.environ["CORE4_OPTION_comoco__history_in_days"] = "!!int 7"
    os.environ["CORE4_OPTION_comoco__precision__year"] = "day"
    os.environ["CORE4_OPTION_comoco__precision__month"] = "hour"
    os.environ["CORE4_OPTION_comoco__precision__day"] = "minute"
    os.environ["CORE4_OPTION_comoco__precision__hour"] = "second"
    os.environ["CORE4_OPTION_comoco__precision__minute"] = "second"
    os.environ["CORE4_OPTION_comoco__precision__second"] = "millisecond"


# =========================================================================== #
# Success pass
# =========================================================================== #

async def test_comoco_history_group_by_day(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_group_by_day")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "endDate=2019-06-18T10:00:00")

    assert response.ok
    assert len(response.json()["data"]) == 3
    assert response.json()["data"][0]["total"] == 4
    assert response.json()["data"][1]["total"] == 9
    assert response.json()["data"][2]["total"] == 10


async def test_comoco_history_group_by_hour(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_group_by_hour")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2019-05-17T00:00:00&"
                                  "endDate=2019-06-18T10:00:00&"
                                  "sort=1")

    assert response.ok
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["total"] == 10


async def test_comoco_history_group_by_minute(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_group_by_minute")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2019-06-16T00:00:00&"
                                  "endDate=2019-06-18T10:00:00&"
                                  "sort=1")

    assert response.ok
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["total"] == 3
    assert response.json()["data"][1]["total"] == 303


async def test_comoco_history_group_by_second(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_group_by_second")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2019-06-18T08:00:00&"
                                  "endDate=2019-06-18T10:00:00&"
                                  "sort=1")

    assert response.ok
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["total"] == 3
    assert response.json()["data"][1]["total"] == 50


async def test_comoco_history_sort_order(core4api, load_db_data):
    # sort in ask order
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_sort_order")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "endDate=2019-06-18T10:00:00&"
                                  "sort=-1")

    assert response.ok
    assert len(response.json()["data"]) == 3
    assert response.json()["data"][0]["total"] == 4
    assert response.json()["data"][1]["total"] == 9
    assert response.json()["data"][2]["total"] == 10

    # sort in ask desk
    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "endDate=2019-06-18T10:00:00&"
                                  "sort=1")

    assert response.ok
    assert len(response.json()["data"]) == 3
    assert response.json()["data"][0]["total"] == 10
    assert response.json()["data"][1]["total"] == 9
    assert response.json()["data"][2]["total"] == 4


async def test_comoco_history_group_by_default_period(core4api, mongodb):
    date_format = "%Y-%m-%dT%H:%M:%S"
    coll = mongodb.sys.event

    nine_days_ago = datetime.datetime.now() - datetime.timedelta(days=9)
    eight_days_ago = datetime.datetime.now() - datetime.timedelta(days=8)
    four_days_ago = datetime.datetime.now() - datetime.timedelta(days=4)
    two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
    today = datetime.datetime.now()

    coll.insert_many([
        {
            "created": nine_days_ago,
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 500
                }
            }
        },
        {
            "created": eight_days_ago,
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 300
                }
            }
        },
        {
            "created": four_days_ago,
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 3
                }
            }
        },
        {
            "created": two_days_ago,
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 2
                }
            }
        },
        {
            "created": today,
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 1
                }
            }
        }
    ])

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?sort=1")

    response_json = response.json()

    assert response.ok
    assert len(response_json["data"]) == 3
    assert response_json["data"][0]["total"] == 3
    assert response_json["data"][1]["total"] == 2
    assert response_json["data"][2]["total"] == 1


async def test_comoco_history_get_some_page(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_get_some_page")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "perPage=1&"
                                  "page=1&"
                                  "sort=1")

    response_json = response.json()

    assert response.ok

    assert response_json["count"] == 1
    assert response_json["page"] == 1
    assert response_json["page_count"] == 3
    assert response_json["total_count"] == 3
    assert response_json["per_page"] == 1

    assert len(response_json["data"]) == 1
    assert response_json["data"][0]["total"] == 2


async def test_comoco_history_response_structure(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_response_structure")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "sort=1")

    response_json = response.json()

    assert response.ok

    assert response_json["count"] == 3
    assert response_json["page"] == 0
    assert response_json["page_count"] == 1
    assert response_json["total_count"] == 3
    assert response_json["per_page"] == 10

    assert len(response_json["data"]) == 3
    assert response_json["data"][0]["total"] == 7
    assert response_json["data"][1]["total"] == 2
    assert response_json["data"][2]["total"] == 15


async def test_comoco_history_different_channel(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(__file__)) + "/test_data/test_comoco_history_different_channel")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "sort=1")

    response_json = response.json()

    assert response.ok

    assert len(response_json["data"]) == 1
    assert response_json["data"][0]["total"] == 1


# =========================================================================== #
# Error pass
# =========================================================================== #


async def test_comoco_history_end_date_lower_then_start_date(core4api, load_db_data):
    load_db_data(os.path.dirname(os.path.abspath(
        __file__)) + "/test_data/test_comoco_history_group_by_day")

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2019-06-18T00:00:00&"
                                  "endDate=2017-01-01T10:00:00")

    assert response.code == 400

# =========================================================================== #
# Performance pass
# =========================================================================== #


async def test_comoco_group_on_a_lot_of_data(core4api, mongodb):
    coll = mongodb.sys.event

    for i in range(100000):
        date_2017 = datetime.datetime(2017,# year
                                      2,# month
                                      2,# day
                                      randint(0, 23),# hour
                                      randint(0, 59),# min
                                      randint(0, 59)) # ms tz

        date_2018 = datetime.datetime(2018, # year
                                      2, # month
                                      2, # day
                                      randint(0, 23), # hour
                                      randint(0, 59), # min
                                      randint(0, 59))  # ms tz

        coll.insert_many([
            {
                "created": date_2017,
                "name": "enqueue_job",
                "channel": "queue",
                "data": {
                    "queue": {
                        "pending": 1,
                        "deferred": 1,
                        "failed": 1,
                        "running": 1,
                        "error": 1,
                        "inactive": 1,
                        "killed": 1
                    }
                }
            },
            {
                "created": date_2018,
                "name": "enqueue_job",
                "channel": "queue",
                "data": {
                    "queue": {
                        "pending": 1,
                        "deferred": 1,
                        "failed": 1,
                        "running": 1,
                        "error": 1,
                        "inactive": 1,
                        "killed": 1
                    }
                }
            }
        ])

    coll.insert_many([
        {
            "created": datetime.datetime(2017, 2, 2),
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 300
                }
            }
        },
        {
            "created": datetime.datetime(2018, 2, 2),
            "name": "enqueue_job",
            "channel": "queue",
            "data": {
                "queue": {
                    "error": 400
                }
            }
        }
    ])

    await core4api.login()

    response = await core4api.get("/core4/api/v1/comoco/history?"
                                  "startDate=2017-01-01T00:00:00&"
                                  "endDate=2019-01-01T00:00:00&"
                                  "sort=1")

    response_json = response.json()

    assert response.ok
    assert len(response_json["data"]) == 2
    assert response_json["data"][0]["total"] == 300
    assert response_json["data"][1]["total"] == 400
