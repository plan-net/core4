# -*- coding: utf-8 -*-

import core4.base.collection
import core4.error
import core4.util
from core4.base.collection import SCHEME


class connect:

    def __init__(self, conn_str):
        self.conn_str = conn_str

        """
        hostname/database/collection
        database/collection
        collection
        """

    def render(self, config):

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
