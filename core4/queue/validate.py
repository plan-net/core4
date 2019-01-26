"""
This module provides various variable type checkers used by :class:`.CoreJob`.
"""

import bson.objectid
from croniter import croniter


# validation helpers

def is_int_gt0(key, val, msg=None):
    """
    Check integer and greater than zero.
    """
    is_int(key, val, msg)
    assert val > 0, msg or "[{}] > 0 expected".format(key)


def is_job(key, val):
    """
    Check this is a :class:`.CoreJob`.
    """
    if val is None:
        return
    msg = "[{}] expected list of CoreJob".format(key)
    assert isinstance(val, list), msg
    if val == []:
        return
    assert set(str) == set([type[d] for d in val]), msg
    # todo: verify job exists
    # todo: decide if dependency is really a str, or can be a job class, too!?


def is_int_gt0_null(key, val):
    """
    Check integer, greater than zero or ``None``.
    """
    if val is None:
        return
    is_int_gt0(key, val, "[{}] > 0 or None expected".format(key))


def is_bool_null(key, val):
    """
    Check boolean or ``None``.
    """
    if val is None:
        return
    assert isinstance(val, bool), "[{}] expected bool".format(key)


def is_str(key, val, msg=None):
    """
    Check str.
    """
    assert isinstance(val, str), msg or "[{}] expected str".format(key)


def is_str_null(key, val):
    """
    Check str or ``None``.
    """
    if val is None:
        return
    is_str(key, val, "[{}] expected str or None".format(key))


def is_int(key, val, msg=None):
    """
    Check integer.
    """
    assert isinstance(val, int), "[{}] expected int".format(key)


def is_cron(key, val):
    """
    Check crontab syntax or ``None``.
    """
    if val is None:
        return
    assert croniter.is_valid(val), "[{}] expected cron syntax or None".format(
        key)


def is_str_list_null(key, val):
    """
    Check lisz of str or ``None``.
    """
    if val is None:
        return
    msg = "[{}] expected list of str or None".format(key)
    assert isinstance(val, list), msg
    if val == []:
        return
    assert set(str) == set([type[d] for d in val]), msg


def is_objectid(key, val):
    """
    Check ObjectId (:mod:`bson.objectid`)
    """
    if val is None:
        return
    msg = "[{}] expected bson.objectid.ObjectId or None".format(key)
    assert isinstance(val, bson.objectid.ObjectId), msg
