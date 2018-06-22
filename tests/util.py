# -*- coding: utf-8 -*-

import os
import pymongo


ASSET_FOLDER = 'asset'
MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4dev'


def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)

def mongo_connect():
    mongo = pymongo.MongoClient(MONGO_URL)
    return mongo[MONGO_DATABASE]