# -*- coding: utf-8 -*-

import pymongo


def make_connection(connection):
    """
    Translates a :class:`.CoreCollection` object into a MongoDB database
    connection.

    :param connection: :class:`.CoreCollection` object
    :return: MongoClient, see :class:`pymongo.mongo_client.MongoClient`
    """
    url = 'mongodb://'
    if connection.username:
        url += connection.username
        if connection.password:
            url += ":" + connection.password
        url += "@"
    url += str(connection.hostname)
    return pymongo.MongoClient(url, tz_aware=False, connect=False)
