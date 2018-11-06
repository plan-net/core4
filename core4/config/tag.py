"""
The :mod:`core4.config.tag` module implements the following helpers with core4
configuration management:

* :func:`connect_database` to create :class:`.CoreCollection` object
* :class:`ConnectTag` to support the custom YAML tag `!!connect`
"""

import yaml

import core4.base.collection
import core4.error
import core4.util
from core4.base.collection import SCHEME


def connect_database(conn_str, async=False, **kwargs):
    """
    This function parses ``conn_str`` parameter and ``kwargs`` default
    parameters and returns :class:`.CoreCollection`. The format of the
    connection string is::

        mongodb://[USERNAME]:[PASSWORD]@<HOSTNAME>:<PORT>/[DATABASE]/<COLLECTION>

    The username, password, hostname, port and database are optional
    parameters. Default parameters for these are expected in ``kwargs``.
    The collection parameter is mandatory.

    :param conn_str: connection string
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
    opts["async"] = async
    if hostname:
        return core4.base.collection.CoreCollection(**opts)
    raise core4.error.Core4ConfigurationError("no mongo connected")
    return None


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

    def connect(self, async=False):
        """
        Used to lazily establish the MongoDB connection when requested. Uses
        :func:`connect_database` to connect.

        :param async: if ``True`` connects with :mod:`motor`, else with
                      :mod:`pymongo` (default).
        :return: :class:`.CoreCollection`
        """

        if self._mongo is None:
            params = {"mongo_url": self.config.get("mongo_url"),
                      "mongo_database": self.config.get("mongo_database"),
                      "async": async}
            self._mongo = connect_database(self.conn_str, **params)
        return self._mongo

    def connect_async(self):
        """
        Same as :meth:`.connect` with ``async=True``.

        :return: :class:`.CoreCollection`
        """
        return self.connect(async=True)

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
