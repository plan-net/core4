import logging
import os

import datetime
import pytest

import core4.logger.mixin
import core4.script.chist
import core4.service.setup
import core4.util.tool

ASSET_FOLDER = '../asset'
MONGO_URL = 'mongodb://core:654321@testmongo:27017'
MONGO_DATABASE = 'core4test'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)


@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    core4.logger.mixin.logon()
    yield
    # run @once methods
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    # singletons
    core4.util.tool.Singleton._instances = {}
    # os environment
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


def test_parse():
    from core4.script.chist import parse_datetime_range
    clock = datetime.datetime(2018, 5, 1, 12, 00, 00)
    assert parse_datetime_range("20:00", "21:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 20, 0),
        datetime.datetime(2018, 4, 30, 21, 0))
    assert parse_datetime_range("13:00", "14:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 13, 0),
        datetime.datetime(2018, 4, 30, 14, 0))
    assert parse_datetime_range("13:00", "8:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 13, 0),
        datetime.datetime(2018, 5, 1, 8, 0))
    assert parse_datetime_range("12:00", "8:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 12, 0),
        datetime.datetime(2018, 5, 1, 8, 0))
    assert parse_datetime_range("8:00", "9:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 8, 0),
        datetime.datetime(2018, 5, 1, 9, 0))
    assert parse_datetime_range("8:00", "18:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 8, 0),
        datetime.datetime(2018, 4, 30, 18, 0))
    assert parse_datetime_range("14:00", "13:00", today=clock) == (
        datetime.datetime(2018, 4, 29, 14, 0),
        datetime.datetime(2018, 4, 30, 13, 0))
    assert parse_datetime_range("8:00", "7:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 8, 0),
        datetime.datetime(2018, 5, 1, 7, 0))
    assert parse_datetime_range("2018-4-30 8:00", "12:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 8, 0),
        datetime.datetime(2018, 4, 30, 12, 0))
    assert parse_datetime_range("2018-4-30 8:00", "13:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 8, 0),
        datetime.datetime(2018, 4, 30, 13, 0))
    assert parse_datetime_range("2018-4-30 16:00", "8:00", today=clock) == (
        datetime.datetime(2018, 4, 30, 16, 0),
        datetime.datetime(2018, 5, 1, 8, 0))
    assert parse_datetime_range("2018-4-30 16:00", "2h", today=clock) == (
        datetime.datetime(2018, 4, 30, 16, 0),
        datetime.datetime(2018, 4, 30, 18, 0))
    assert parse_datetime_range("2018-4-30 16:00", "2d", today=clock) == (
        datetime.datetime(2018, 4, 30, 16, 0),
        datetime.datetime(2018, 5, 2, 16, 0))
    assert parse_datetime_range("2018-4-30 16:00", "2019-4-30 18:00",
                                today=clock) == (
               datetime.datetime(2018, 4, 30, 16, 0),
               datetime.datetime(2019, 4, 30, 18, 0))
    assert parse_datetime_range("6h", "11:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 1, 11, 0))
    assert parse_datetime_range("6h", "13:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 1, 13, 0))
    assert parse_datetime_range("6h", "5:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 2, 5, 0))
    assert parse_datetime_range("6h", "2018 5 1 11:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 1, 11, 0))
    assert parse_datetime_range("6h", "2018 5 1 18:00", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 1, 18, 0))
    with pytest.raises(ValueError):
        parse_datetime_range("6h", "2018 5 1 3:00", today=clock)
    assert parse_datetime_range("6h", "6h", today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0),
        datetime.datetime(2018, 5, 1, 12, 0))
    assert parse_datetime_range("6h", None, today=clock) == (
        datetime.datetime(2018, 5, 1, 6, 0), None)
    assert parse_datetime_range("11:00", None, today=clock) == (
        datetime.datetime(2018, 5, 1, 11, 0), None)
    assert parse_datetime_range("16:00", None, today=clock) == (
        datetime.datetime(2018, 4, 30, 16, 0), None)
    assert parse_datetime_range("2018-1-12 16:00", None, today=clock) == (
        datetime.datetime(2018, 1, 12, 16, 0), None)
    with pytest.raises(ValueError):
        parse_datetime_range(None, "2018-1-12 16:00", today=clock)


def test_main():
    from core4.script.chist import build_query
    clock = datetime.datetime(2018, 5, 1, 12, 00, 00)

    q = build_query({}, clock=clock, utc=False)
    assert q == [{'created': {'$gte': datetime.datetime(2018, 5, 1, 11, 0)}}]

    q = build_query({"--start": "6h", "--end": "2h"}, clock=clock, utc=False)
    assert q == [{'created': {'$gte': datetime.datetime(2018, 5, 1, 6, 0)}},
                 {'created': {'$lt': datetime.datetime(2018, 5, 1, 8, 0)}}]

    q = build_query({"--level": "i"}, clock=clock, utc=False)
    assert q == [{'created': {'$gte': datetime.datetime(2018, 5, 1, 11, 0)}},
                 {'levelno': {'$gte': 20}}]

    with pytest.raises(SystemExit):
        build_query({"--level": "x"}, clock=clock)
