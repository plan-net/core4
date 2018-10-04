import os

import bson.objectid


# validation helpers

def is_int_gt0(key, val, msg=None):
    is_int(key, val, msg)
    assert val > 0, msg or "[{}] > 0 expected".format(key)


def is_job(key, val):
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
    if val is None:
        return
    is_int_gt0(key, val, "[{}] > 0 or None expected".format(key))


def is_bool_null(key, val):
    if val is None:
        return
    assert isinstance(val, bool), "[{}] expected bool".format(key)


def is_str(key, val, msg=None):
    assert isinstance(val, str), msg or "[{}] expected str".format(key)


def is_str_null(key, val):
    if val is None:
        return
    is_str(key, val, "[{}] expected str or None".format(key))


def is_int(key, val, msg=None):
    assert isinstance(val, int), "[{}] expected int".format(key)


def is_cron(key, val):
    if val is None:
        return
    is_str(key, val, "[{}] expected cron syntax or None".format(key))
    # todo: check crontab format (later)


def is_str_list_null(key, val):
    if val is None:
        return
    msg = "[{}] expected list of str or None".format(key)
    assert isinstance(val, list), msg
    if val == []:
        return
    assert set(str) == set([type[d] for d in val]), msg


def is_objectid(key, val):
    if val is None:
        return
    msg = "[{}] expected bson.objectid.ObjectId or None".format(key)
    assert isinstance(val, bson.objectid.ObjectId), msg


def exists(key, val):
    if val is None:
        return
    msg = "[{}] expected Python executable or None".format(key)
    assert os.path.exists(val), msg
