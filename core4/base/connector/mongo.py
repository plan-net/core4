import pymongo
import motor

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
             object has ``connection.async == True``.
    """
    global CACHE
    url = 'mongodb://'
    if connection.username:
        url += connection.username
        if connection.password:
            url += ":" + connection.password
        url += "@"
    url += str(connection.hostname)
    if connection.async:
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
