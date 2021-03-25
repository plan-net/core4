#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
General purpose data management helpers.
"""
import datetime
import gzip
import json
import os
import textwrap
from io import StringIO

import bson.objectid
import docutils.parsers.rst.directives.body
import docutils.parsers.rst.roles
import numpy as np
import pandas as pd
import pytz
import sphinx.ext.napoleon
import tzlocal
from docutils import core
from docutils.parsers.rst.directives import register_directive

LOCAL_TZ = lambda: pytz.timezone(tzlocal.get_localzone().zone)

NAPOLEON = sphinx.ext.napoleon.Config(
    napoleon_use_param=False,
    napoleon_use_rtype=True,
    napoleon_google_docstring=True,
    napoleon_numpy_docstring=False,
    napoleon_include_init_with_doc=True,
    napoleon_include_private_with_doc=True,
    napoleon_include_special_with_doc=True,
    napoleon_use_admonition_for_examples=False,
    napoleon_use_admonition_for_notes=True,
    napoleon_use_admonition_for_references=True,
    napoleon_use_ivar=True,
    napoleon_use_keyword=True
)

register_directive("method", docutils.parsers.rst.directives.body.Rubric)
for role in ("exc", "meth", "mod", "class", "ref", "doc", "attr"):
    docutils.parsers.rst.roles.register_local_role(
        role, docutils.parsers.rst.roles.generic_custom_role)


def dfutc2local(col):
    """
    Convert :mod:`pandas` timeseries in UTC into local date/time.


    :param col: class:`pandas.core.series.Series` without timezone information
    :return: local class:`pandas.core.series.Series` without timezone
    """
    return col.dt.tz_localize("UTC").dt.tz_convert(
        LOCAL_TZ()).dt.tz_localize(None)


def utc2local(dt):
    """
    Convert :class:`datetime.datetime` in UTC into local date/time.

    :param col: class:`datetime.datetime` without timezone information
    :return: local class:`datetime.datetime` without timezone
    """
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(
        LOCAL_TZ()).replace(tzinfo=None)


def local2utc(dt):
    """
    Convert local :class:`datetime.datetime` to UTC.

    :param col: class:`datetime.datetime` without timezone information
    :return: class:`datetime.datetime` without timezone in UTC
    """
    local_dt = LOCAL_TZ().localize(dt, is_dst=None)
    return local_dt.astimezone(pytz.utc)


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
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
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


def rst2html(doc):
    """
    Parses the doc string using sphinx with napoleon extension.

    :param doc: docstring
    :return: dict with keys ``body`` (html) and ``error`` (list of parsing
             errors)
    """
    dedent = textwrap.dedent(doc)
    google = sphinx.ext.napoleon.GoogleDocstring(
        docstring=dedent, config=NAPOLEON)
    err = StringIO()
    parts = core.publish_parts(source=str(google), writer_name="html",
                               settings_overrides=dict(warning_stream=err))
    err.seek(0)
    errors = [line for line in err.read().split("\n") if line.strip()]
    return {
        'error': errors,
        'body': parts['fragment']
    }


def compress(filename):
    """
    Compress a file.

    :param filename: full filename
    :return: compressed full filename
    """
    target = filename + '.gz'
    fin = open(filename, 'rb')
    fout = gzip.open(target, 'wb')
    fout.writelines(fin)
    fout.close()
    fin.close()
    os.remove(filename)
    return target
