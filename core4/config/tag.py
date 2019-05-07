#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
The :mod:`core4.config.tag` module implements the following helpers with core4
configuration management:

* :func:`connect_database` to create :class:`.CoreCollection` object
* :class:`ConnectTag` to support the custom YAML tag `!!connect`
* :class:`JobConnectTag` for special handling of custom YAML tag `!!connect`
  with :class:`.CoreJob` classes
"""

import yaml

import core4.base.collection
import core4.error
from core4.base.collection import SCHEME

def connect_database(conn_str, callback, concurr=False, **kwargs):
    """
    This function parses ``conn_str`` parameter and ``kwargs`` default
    parameters and returns :class:`.CoreCollection`. The format of the
    connection string is::

        mongodb://[USERNAME]:[PASSWORD]@<HOSTNAME>:<PORT>/[DATABASE]/<COLLECTION>

    The username, password, hostname, port and database are optional
    parameters. Default parameters for these are expected in ``kwargs``.
    The collection parameter is mandatory.

    :param conn_str: connection string
    :param callback: function to return the collection object
    :param mongo_url: default ``mongo_url``
    :param mongo_database: default ``mongo_database``
    :return: :class:`.CoreCollection` object
    """
    (protocol, *specs) = conn_str.split("://")
    specs = specs[0]
    opts = dict()
    opts["scheme"] = protocol
    if ((kwargs.get(SCHEME[opts["scheme"]]["url"]) is not None)
            and (not isinstance(
                kwargs.get(SCHEME[opts["scheme"]]["url"]), str))):
        raise core4.error.Core4ConfigurationError("[mongo_url] expected str")
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
    opts["async_conn"] = concurr
    if hostname:
        return callback(**opts)
    raise core4.error.Core4ConfigurationError("no mongo connected")


class ConnectTag(yaml.YAMLObject):
    """
    This class implements the custom YAML tag ``!connect``. See
    :func:`connect_database` about the format of the connection string.

    This method implements the delegation pattern and passes all non-owned
    methods and properties to :class:`.CoreCollection`.
    """

    yaml_tag = u'!connect'

    def __init__(self, conn_str):
        """
        Initialises the MongoDB connection. The connection is instantiated
        after complete core4 configuration is provided with
        :meth:`.set_config`.

        :param conn_str: connection string, see :func:`connect_database``
        """
        if conn_str.count("://") == 0:
            raise core4.error.Core4ConfigurationError(
                "malformed connection string [{}]".format(conn_str))
        self.conn_str = conn_str
        self.concurr = None
        self._mongo = None

    def __repr__(self):
        """
        :return: string representation of the tag
        """
        return "!connect '" + self.conn_str + "'"

    def set_config(self, config):
        """
        Passes the current core4 configuration to lazily establish the
        MongoDB connection

        :param config: core4 configuration dict
        """
        self.config = config

    def set_connect(self, concurr):
        self.concurr = concurr

    def init_collection(self, **kwargs):
        """
        Default initiator of the :class:`.CoreCollection` object.

        :param kwargs: to be passed to :class:`.CoreCollection`
        :return: :class:`.CoreCollection` instance
        """
        return core4.base.collection.CoreCollection(**kwargs)

    def connect(self, concurr=None):
        """
        Used to lazily establish the MongoDB connection when requested. Uses
        :func:`connect_database` to connect.

        :param concurr: if ``True`` connects with :mod:`motor`, else with
                      :mod:`pymongo` (default).
        :return: :class:`.CoreCollection`
        """
        if self._mongo is None:
            params = {"mongo_url": self.config.get("mongo_url"),
                      "mongo_database": self.config.get("mongo_database")}
            if concurr is not None:
                params["concurr"] = concurr
            else:
                params["concurr"] = self.concurr
            self._mongo = connect_database(self.conn_str, self.init_collection,
                                           **params)
        return self._mongo

    def connect_async(self):
        """
        Same as :meth:`.connect` with ``concurr=True``.

        :return: :class:`.CoreCollection`
        """
        return self.connect(concurr=True)

    def connect_sync(self):
        """
        Same as :meth:`.connect` with ``concurr=False``.

        :return: :class:`.CoreCollection`
        """
        return self.connect(concurr=False)

    def __getattr__(self, item):
        return getattr(self.connect(), item)

    @classmethod
    def from_yaml(cls, loader, node):
        """
        Class method used to parse the `!connect` YAML tag.

        :param loader: YAML loader, see :mod:`PyYAML`
        :param node: current YAML node
        :return: :class:`.ConnectTag`
        """
        return ConnectTag(node.value)


class JobConnectTag(ConnectTag):
    """
    Derived from :class:`.ConnectTag` for :class:`.CoreJob` to connect to
    MongoDB. This special tag class features the link between jobs and
    MongoDB collection objects by document properties ``_job_id`` and ``_src``.
    """

    def __init__(self, conn_str, job, *args, **kwargs):
        """
        Initialises the MongoDB connection and links the passed job object.

        :param conn_str: connection string, see :func:`connect_database``
        :param job: :class:`.CoreJob` object
        """
        super().__init__(conn_str, *args, **kwargs)
        self.job = job

    def init_collection(self, **kwargs):
        """
        Default initiator of the special :class:`.CoreJobCollection` object.

        :param kwargs: to be passed to :class:`.CoreJobCollection`
        :return: :class:`.CoreCollection` instance
        """
        coll = core4.base.collection.CoreJobCollection(**kwargs)
        coll.set_job(self.job)
        return coll

    def set_job(self, job):
        """
        Assign the passed job to :class:`.CoreJobCollection` object.

        :param job: :class:`.CoreJob` object
        """
        job.logger.debug("set job to [%s] at [%s]", self.__class__.__name__,
                         self.conn_str)
        self.job = job
        if self._mongo is not None:
            self._mongo.set_job(job)
