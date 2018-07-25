# -*- coding: utf-8 -*-

"""
The :mod:`core4.config.pragma` module implements the following helpers with
core4 configuration management:

* :class:`connect` to specify :class:`.CoreCollection` connection settings

"""


import core4.base.collection
import core4.error
import core4.util
from core4.base.collection import SCHEME


class connect:

    """
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

        mongo_url = "mongodb://user:pwd@localhost:27017"
        mongo_database = "testdb"

        section1 = {
            result1 = connect("mongodb://user:pwd@localhost:27017/testdb/result")
            result2 = connect("mongodb://testdb/result")
            result3 = connect("mongodb://result")
        }

    Access to this configuration example proofs that all three
    :class:`.CoreCollection` objects constructed with the :class:`.connect`
    statement point to the same MongoDB collection::

        c = conf.section1
        c.result1.info_url == c.result2.info_url == c.result3.info_url
    """
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def render(self, config):
        """
        This method is used by :meth:`._explode` to render the
        :class:`connect` statement into a :class:`.CoreCollection` object with
        direct data access.

        :param config: reference to :class:`.CoreConfig` object to provide
                       configuration access
        :return: :class:`.CoreCollection` object
        """

        conn = self.conn_str
        if conn.count("://") == 0:
            raise core4.error.Core4ConfigurationError(
                "malformed collection connection string [{}]".format(conn))

        (protocol, *specs) = conn.split("://")
        specs = specs[0]
        opts = dict()
        opts["scheme"] = protocol

        default_url = config[SCHEME[opts["scheme"]]["url"]][len(protocol) + 3:]
        default_database = config[SCHEME[opts["scheme"]]["database"]]

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
                "malformed collection connection string [{}]".format(conn))

        if hostname.count("@") > 0:
            (auth, *address) = hostname.split("@")
            (username, *password) = auth.split(":")
            opts["username"] = username
            opts["password"] = ":".join(password)
            hostname = "@".join(address)

        opts["hostname"] = hostname
        opts["database"] = database
        opts["collection"] = "/".join(collection)

        return core4.base.collection.CoreCollection(**opts)
