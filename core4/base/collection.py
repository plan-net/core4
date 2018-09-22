"""
This module implements CoreCollection, featuring database access.
"""

import core4.error
from core4.base.connector.mongo import make_connection as make_mongo_connection

DEFAULT_SCHEME = 'mongodb'
SCHEME = {
    'mongodb': {
        'database': 'mongo_database',
        'url': 'mongo_url',
        'connector': make_mongo_connection
    }
}


class CoreCollection:
    """
    This class encapsulates data access.
    """

    def __init__(
            self, scheme, hostname, database, collection, username=None,
            password=None):
        """
        Instantiates a CoreCollection object with

        :param scheme: at the moment only mongodb is supported
        :param hostname: (str)
        :param database: name (str)
        :param collection: name (str)
        :param username: (str)
        :param password: (str)
        """
        self.scheme = scheme
        self.hostname = hostname
        self.database = database
        self.collection = collection
        self.username = username
        self.password = password
        self._connection = None
        if self.scheme not in SCHEME:
            raise core4.error.Core4ConfigurationError(
                "unknown scheme [{}]".format(self.scheme))

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

        #. ``mongodb://`` with MongoDB

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
        loc += str(self.hostname)
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
