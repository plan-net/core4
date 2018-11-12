import json

import bson.objectid
import datetime
import numpy as np
import pandas as pd

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


def parse_boolean(value, error=False):
    """
    Translates the passed value into a bool. With ``error == False`` (default)
    and no pattern for ``True`` or ``False`` matches the passed value, then the
    actual value is returned. With ``error == True`` the method raises a
    :class:`TypeError` if no valid representative for ``True``/``False`` is
    provided.

    Valid strings are (case insensitive):

    * yes/no
    * y/n
    * on/off
    * true/false
    * t/f

    :param value: string representing ``True`` or ``False``
    :return: evaluated string as ``True`` or ``False`` or the original string
             value no pattern matches.
    """
    if value.lower() in ("yes", "y", "on", "1", "true", "t"):
        return True
    elif value.lower() in ("no", "n", "off", "0", "false", "f"):
        return False
    if error:
        raise TypeError("failed to parse bool from [%s]" % value)
    return value


class JsonEncoder(json.JSONEncoder):
    """
    Encodes Python dictionaries into JSON. Beyond the :mod:`json` encoder this
    class supports the following additional types:

    * :class:`datetime.datetime` and :class:`numpy.datetime64` into ISO format
    * :class:`bson.objectid.ObjectId` into str
    * :mod:`numpy` conversion of bool, integer, floating and ndarray
    """
    def default(self, obj):
        if isinstance(obj, np.datetime64):
            # this is a hack around pandas bug, see
            # http://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64/13753918
            # we only observe this conversion requirements for dataframes with one and only one datetime column
            obj = pd.to_datetime(str(obj)).replace(tzinfo=None)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        # what follows is based on
        # http://stackoverflow.com/questions/27050108/convert-numpy-type-to-python
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def json_encode(value, **kwargs):
    """
    JSON-encodes the given Python object using :class:`.JsonEncoder`.

    :param value: dict to convert
    :param kwargs: additional keyword arguments to be passed to
                   :class:`.JsonEncoder`
    :return: str representing JSON
    """
    return json.dumps(value, cls=JsonEncoder, **kwargs)


def json_decode(value, **kwargs):
    """
    JSON-decods the given str into a Python dictionary using
    :mod:`.json`.

    :param value: str representing valid JSON
    :param kwargs: additional keyword arguments to be passed to
                   :mod:`json`
    :return: dict or ``None`` if ``value`` is empty or ``None``
    """
    if value:
        return json.loads(value, **kwargs)
    return None