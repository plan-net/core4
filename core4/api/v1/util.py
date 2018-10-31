"""
Utility methods in the context of core4 API.
"""

import json

import bson.objectid
import datetime
import numpy as np
import pandas as pd


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
