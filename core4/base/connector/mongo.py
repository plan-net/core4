#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Delivers MongoDB cached database connectivity using :mod:`pymongo` and
:mod:`motor`.
"""

import motor
import pymongo

CACHE = {
    'sync': {},
    "async": {}
}


def make_connection(connection):
    """
    Translates a :class:`.CoreCollection` object into a synchronous or
    asynchronos MongoDB database connection.

    :param connection: :class:`.CoreCollection` object
    :return: MongoClient, see :class:`pymongo.mongo_client.MongoClient`
             or MotorClient, see :class:`motor.MotorClient` if the connection
             object has ``connection.async_conn == True``.
    """
    global CACHE
    url = 'mongodb://'
    if connection.username:
        url += connection.username
        if connection.password:
            url += ":" + connection.password
        url += "@"
    url += str(connection.hostname)
    if connection.async_conn:
        mode = "async"
    else:
        mode = "sync"
    if url in CACHE[mode]:
        return CACHE[mode][url]
    if connection.async:
        CACHE[mode][url] = motor.MotorClient(
            url, tz_aware=False, connect=False)
    else:
        CACHE[mode][url] = pymongo.MongoClient(
            url, tz_aware=False, connect=False)
    return CACHE[mode][url]
