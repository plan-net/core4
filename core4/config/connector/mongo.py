# -*- coding: utf-8 -*-

import pymongo


def connect(connection):
    url = 'mongodb://'
    if connection.username:
        url += connection.username
        if connection.password:
            url += ":" + connection.password
        url += "@"
    url += connection.hostname
    return pymongo.MongoClient(url, tz_aware=False, connect=False)
