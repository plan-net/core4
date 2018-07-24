# -*- coding: utf-8 -*-

"""
This module implements CoreCollection, featuring database access.
"""

from core4.base.connector.mongo import make_connection as make_mongo_connection

DEFAULT_SCHEME = 'mongodb'
SCHEME = {
    'mongodb': {
        'database': 'mongo_database',
        'url': 'mongo_url',
        'connector': make_mongo_connection
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
        """
        Database connection factory, featuring the following protocols:

        #. MongoDB

        :return: database connection
        """
        if self._connection is None:
            connector = SCHEME[self.scheme]['connector']
            self._connection = connector(self)
        return self._connection

    @property
    def info_url(self):
        """
        human-readable connection string hiding sensitive data, e.g.
        password, from inquisitive eyes.

        :return: connection URL information (str)
        """
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
        """
        Delegates all methods and attributes to the database object.
        """
        return getattr(self.connection[self.database][self.collection], item)
