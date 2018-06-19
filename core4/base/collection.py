# -*- coding: utf-8 -*-

from core4.base.connector.mongo import connect as mongo_connect

DEFAULT_SCHEME = 'mongodb'
SCHEME = {
    'mongodb': {
        'database': 'mongo_database',
        'url': 'mongo_url',
        'connector': mongo_connect
    },
    # 'postgres': {
    #     'database': 'postgres_database',
    #     'url': 'postgres_url',
    #     'connector': postgres_connect
    # }
}


class CoreCollection:
    """
    This class encapsulates data access to MongoDB collections.
    """

    def __init__(
            self, scheme, hostname, database, collection, username=None,
            password=None):
        self.scheme = scheme
        self.hostname = hostname
        self.database = database
        self.collection = collection
        self.username = username
        self.password = password
        self._connection = None

    def __repr__(self):
        return "CoreConnection(" \
               "scheme='{scheme}', " \
               "hostname='{hostname}', " \
               "username='{username}', " \
               "database='{database}', " \
               "collection='{collection}'" \
               ")".format(**self.__dict__)

    @property
    def connection(self):
        if self._connection is None:
            connector = SCHEME[self.scheme]['connector']
            self._connection = connector(self)
        return self._connection

    @property
    def info_url(self):
        loc = ""
        if self.username:
            loc += self.username + "@"
        loc += self.hostname
        if self.database:
            loc += "/" + self.database
        if self.collection:
            loc += "/" + self.collection
        return loc

    def __getattr__(self, item):
        return getattr(self.connection[self.database][self.collection], item)
