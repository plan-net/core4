"""
This module implements CoreCollection, featuring database access.
"""

import core4.error
import pymongo.collection
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
            password=None, async=False):
        """
        Instantiates a CoreCollection object with

        :param scheme: at the moment only mongodb is supported
        :param hostname: (str)
        :param database: name (str)
        :param collection: name (str)
        :param username: (str)
        :param password: (str)
        :param async: (bool)
        """
        self.scheme = scheme
        self.hostname = hostname
        self.database = database
        self.collection = collection
        self.username = username
        self.password = password
        self._connection = None
        self.async = async
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
        Database connection factory, featuring the following protocols::

            mongodb://  # MongoDB

        :return: database connection
        """
        if self._connection is None:
            connector = SCHEME[self.scheme]['connector']
            self._connection = connector(self)
        return self._connection

    @property
    def info_url(self):
        """
        Human-readable connection string hiding sensitive data, e.g.
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


class JobCollection(pymongo.collection.Collection):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_job(self, _id, _src):
        if _id is None:
            raise AttributeError("_id must not be None")
        if _src is None:
            raise AttributeError("_src must not be None")
        self._job = {
            "_job_id": _id,
            "_src": _src
        }

    def insert_one(self, document, *args, **kwargs):
        document.update(self._job)
        return super().insert_one(document, *args, **kwargs)

    def insert_many(self, documents, *args, **kwargs):
        for i in range(len(documents)):
            documents[i].update(self._job)
        return super().insert_many(documents, *args, **kwargs)

    def bulk_write(self, requests, *args, **kwargs):
        for i in range(len(requests)):
            if hasattr(requests[i], "_doc"):
                requests[i]._doc.update(self._job)
        return super().bulk_write(requests, *args, **kwargs)

    def _update(self, sock_info, criteria, document, *args, **kwargs):
        if "$set" in document:
            document["$set"].update(self._job)
        else:
            document["$set"] = self._job
        super()._update(sock_info, criteria, document, *args, **kwargs)


class CoreJobCollection(CoreCollection):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._job = None

    def __getattr__(self, item):
        coll = JobCollection(self.connection[self.database], self.collection)
        coll.set_job(self._job._id, self._job.get_source())
        return getattr(coll, item)

    def set_job(self, job):
        job.logger.debug("set job to connect with [%s]", self.info_url)
        self._job = job
