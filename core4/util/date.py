import datetime

LOCAL_TZ = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


def dfutc2local(col):
    """
    Convert :mod:`pandas` timeseries in UTC into local date/time.


    :param col: class:`pandas.core.series.Series` without timezone information
    :return: local class:`pandas.core.series.Series` without timezone
    """
    # todo: is this really really really necessary:
    #       add UTC info, convert to local timezone, and remove tz info?
    return col.dt.tz_localize("UTC").dt.tz_convert(
        LOCAL_TZ).dt.tz_localize(None)


def utc2local(dt):
    """
    Convert :class:`datetime.datetime` in UTC into local date/time.

    :param col: class:`datetime.datetime` without timezone information
    :return: local class:`datetime.datetime` without timezone
    """
    # todo: is this really really really necessary:
    #       add UTC info, convert to local timezone, and remove tz info?
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(
        LOCAL_TZ).replace(tzinfo=None)