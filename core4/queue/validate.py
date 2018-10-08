
# validation helpers

def is_int_gt0(key, val, msg=None):
    is_int(key, val)
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
    is_int_gt0(val, "[{}] > 0 or None expected".format(key))


def is_bool_null(key, val):
    if val is None:
        return
    assert isinstance(val, bool), "[{}] expected bool".format(key)


def is_str(key, val, msg=None):
    assert isinstance(val, str), msg or "[{}] expected str".format(key)


def is_str_null(key, val):
    if val is None:
        return
    is_str(val, "[{}] expected str or None".format(key))


def is_int(key, val):
    assert isinstance(val, int), "[{}] expected int".format(key)


def is_cron(key, val):
    if val is None:
        return
    is_str(val, "[{}] expected cron syntax or None".format(key))
    # todo: check crontab format (later)


def is_str_list_null(key, val):
    if val is None:
        return
    msg = "[{}] expected list of str or None".format(key)
    assert isinstance(val, list), msg
    if val == []:
        return
    assert set(str) == set([type[d] for d in val]), msg

