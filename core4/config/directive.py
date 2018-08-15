# -*- coding: utf-8 -*-

"""
The :mod:`core4.config.directive` module implements the following helpers with
core4 configuration management:

* :class:`connect` to specify :class:`.CoreCollection` connection settings

Use the ``connect(conn_str)`` statement to spefify :class:`.CoreCollection`
connections. The ``connect`` statement parses authentication/hostname
information, database and collection name.

A fully qualified connection string to a MongoDB database ``testdb``,
collection ``result`` at ``localhost``, port ``27017``, authenticated with
username ``user`` and password ``pwd`` is::

    target = connect("mongodb://user:pwd@localhost:27017/testdb/result")

If no hostname is specified, then the connection URL is taken from variable
``mongo_url``. If no database name is specified, then it is taken from
variable ``mongo_database``. Therefore, the following three examples all
cascade to the same connection settings::

    from core4.config import connect

    mongo_url = "mongodb://usr:pwd@localhost:27017"
    mongo_database = "db"

    section1 = dict(
        result1 = connect("mongodb://usr:pwd@localhost:27017/db/result"),
        result2 = connect("mongodb://db/result"),
        result3 = connect("mongodb://result")
    )

Access to this configuration example proofs that all three
:class:`.CoreCollection` objects constructed with the :class:`.connect`
statement point to the same MongoDB collection::

    c = conf.section1
    c.result1.info_url == c.result2.info_url == c.result3.info_url
"""

import yaml

import core4.base.collection
import core4.error
import core4.util
from core4.base.collection import SCHEME
import os


def connect_mongodb(conn_str, **kwargs):
    (protocol, *specs) = conn_str.split("://")
    specs = specs[0]
    opts = dict()
    opts["scheme"] = protocol
    default_url = kwargs.get(SCHEME[opts["scheme"]]["url"])
    if default_url is not None and default_url.startswith(protocol):
        default_url = default_url[len(protocol) + 3:]
    default_database = kwargs.get(SCHEME[opts["scheme"]]["database"])

    level = specs.count("/")
    if level == 2:
        (hostname, database, *collection) = specs.split("/")
    elif level == 1:
        (database, *collection) = specs.split("/")
        hostname = default_url
    elif level == 0:
        collection = [specs]
        database = default_database
        hostname = default_url
    elif level > 2:
        raise core4.error.Core4ConfigurationError(
            "malformed collection connection string [{}]".format(conn_str))

    if hostname is not None and hostname.count("@") > 0:
        (auth, *address) = hostname.split("@")
        (username, *password) = auth.split(":")
        opts["username"] = username
        opts["password"] = ":".join(password)
        hostname = "@".join(address)

    opts["hostname"] = hostname
    opts["database"] = database
    opts["collection"] = "/".join(collection)
    if hostname:
        return core4.base.collection.CoreCollection(**opts)
    return None


class ConnectTag(yaml.YAMLObject):
    yaml_tag = u'!connect'

    def __init__(self, conn_str):
        if conn_str.count("://") == 0:
            raise core4.error.Core4ConfigurationError(
                "malformed connection string [{}]".format(conn_str))
        self.conn_str = conn_str
        self._mongo = None

    def __repr__(self):
        return "!connect '" + self.conn_str + "'"

    def set_config(self, config):
        self.config = config

    def _connect(self):
        if self._mongo is None:
            kwargs = {
                "mongo_url": self.config.get("mongo_url"),
                "mongo_database": self.config.get("mongo_database")
            }
            self._mongo = connect_mongodb(self.conn_str, **kwargs)
        return self._mongo

    def __getattr__(self, item):
        return getattr(self._connect(), item)

    @classmethod
    def from_yaml(cls, loader, node):
        return ConnectTag(node.value)

# def load_yaml(stream, config):
#     loader = SafeLoader(stream)
#     loader._config = config
#     try:
#         return loader.get_single_data()
#     finally:
#         loader.dispose()
