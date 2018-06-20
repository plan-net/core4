# -*- coding: utf-8 -*-

import configparser
import os
import urllib.parse
import oyaml

import dateutil.parser
import pkg_resources

import core4.base.collection
import core4.util
from core4.base.collection import DEFAULT_SCHEME, SCHEME

# config locations, see https://pypi.org/project/appdirs/1.4.0/
EXTENDED_INTERPOLATION = False
DEFAULT_CONFIG = pkg_resources.resource_filename("core4", "config/core.yaml")
LOCAL_USER_BASENAME = (os.path.expanduser("core4"), "local")
SYSTEM_BASENAME = ("/etc/core4", "local")
CONFIG_EXTENSION = {
    (".ini", ".conf"): "ini",
    (".yaml", ".yml"): "yaml"
}


def find_config_file(dir, basename):
    for (extlist, ty) in CONFIG_EXTENSION.items():
        for e in extlist:
            fn = os.path.join(dir, basename + e)
            if os.path.exists(fn):
                return (fn, ty)
    return None


class CoreConfig:
    """
    This class is the gateway into core4 configuration. It is implemented as a
    proxy to :class:`configparser.ConfigParser` with a defined set of
    configuration sources and a primary section.

    The proxy object

    #. forwards methods :meth:`~configparser.ConfigParser.defaults`,
       :meth:`~configparser.ConfigParser.sections`,
       :meth:`~configparser.ConfigParser.has_section` and
       :meth:`~configparser.ConfigParser.options`
    #. wraps methods :meth:`~configparser.ConfigParser.get`,
       :meth:`~configparser.ConfigParser.getint`,
       :meth:`~configparser.ConfigParser.getfloat`,
       :meth:`~configparser.ConfigParser.getboolean`,
       :meth:`~configparser.ConfigParser.has_option`
       with the specified section or the :ref:`primary_section`
    #. extends the standard parser with methods
       :meth:`~.CoreConfig.get_datetime`, :meth:`~.CoreConfig.get_regex`, and
       :meth:`~.CoreConfig.get_collection`
    #. hides all other methods

    By default the :class:`CoreConfig` object uses
    :class:`~configparser.BasicInterpolation`. You can change this behavior to
    :class:`~configparser.ExtendedInterpolation` with the ``extended``
    parameter. This feature is considered experimental.

    :class:`.CoreConfig` implements class-level caching of plugin based
    configuration and mongo config collection. Purge the cache with the
    class method :meth:`~.CoreConfig.purge_cache`.
    """

    _WRAP = ["get", "getint", "getfloat", "getboolean", "has_option"]
    _FORWARD = ["defaults", "sections"]

    # special implement with .options(), .has_section()

    default_config = DEFAULT_CONFIG
    user_config = LOCAL_USER_BASENAME
    system_config = SYSTEM_BASENAME

    _cache = {}
    _db_cache = None

    def __init__(
            self, section="DEFAULT", extra_config=None, config_file=None,
            extended=EXTENDED_INTERPOLATION):
        """
        Creates the config object loaded from

        #. core4's **default** configuration file (./core4/config/core.yaml)
        #. an **extra** configuration file (defaults to None)
        #. a **local** configuration file (by OS environment
           variable ``CORE4_CONFIG``, or from the user's home
           directory ``~/.core/local.yaml``, or from the system
           directory ``/etc/core/local.yaml``, or from collection
           ``core4.sys.config``. The first existing config provider
           wins and local configuration processing stops.
        #. OS environment variables following the naming convention
           ``CORE4_[SECTION]__[OPTION]`` (watch the double
           underscore between section and option) are applied as the
           final step to load core4 configuration.

        Raises FileNotFoundError if an expected configuration file
        has not been found.

        :param section: :ref:`primary_section`, defaults to ``DEFAULT``
        :param extra_config: extra configuration file
        :param config_file: forced configuration file; if defined skips the
                            cascade of ``CORE4_CONFIG`` variable, the user's
                            and the system`s configuration file
        :param extended: uses :class:`configparser.ExtendedInterpolation`
                         instead of the default
                         :class:`configparser.BasicInterpolation`
        """
        self._config_file = config_file
        self.extra_config = extra_config
        self.primary = section
        self.env_config = os.getenv("CORE4_CONFIG", None)
        self._extended = extended
        self._config = None
        self._path = []

    @classmethod
    def purge_cache(cls):
        """
        purges and class-level cache
        """
        cls._cache = {}
        cls._db_conf = None

    @property
    def config(self):
        """
        provides lazy access to :class:`~configparser.ConfigParser`

        :return: :class:`~configparser.ConfigParser` object
        """
        if self._config is None:
            # extra_config only drives the caching
            cache_item = str(self.extra_config)
            if cache_item in self.__class__._cache:
                return self.__class__._cache[cache_item]
            kwargs = dict(allow_no_value=True)
            if self._extended:
                kwargs["interpolation"] = configparser.ExtendedInterpolation()
            self._config = configparser.ConfigParser(**kwargs)
            # step #1: core configuration
            self._read_file(self.default_config)
            # step #2: extra configuration
            if self.extra_config:
                self._read_file(self.extra_config)
            # step #3: local configuration
            if self._config_file:
                self._read_file(self._config_file)
            elif self.env_config:
                # by OS environment variable CORE_CONFIG
                self._read_file(self.env_config)
            else:
                user_config = find_config_file(*self.user_config)
                if user_config:
                    # in user's home directory ~/
                    self._read_file(user_config[0])
                else:
                    system_config = find_config_file(*self.system_config)
                    if system_config:
                        # in system configuration directory /etc
                        self._read_file(system_config[0])
            # in core4 system collection sys.config
            self._read_db()
            # post process single OS environment variables
            self._read_environment()
            self.__class__._cache[cache_item] = self._config
        return self._config

    def _read_file(self, filename):
        if os.path.exists(filename):
            ext = os.path.splitext(filename)[1]
            found = [j for i, j in CONFIG_EXTENSION.items() if ext in i]
            if not found:
                raise KeyError("unknown file type of {}".format(filename))
            if found[0] == "yaml":
                with open(filename, 'r', encoding='utf-8') as stream:
                    data = oyaml.load(stream)
                    self._config.read_dict(data)
            else:
                self._config.read(filename)
            self._path.append(filename)
        else:
            raise FileNotFoundError(filename)

    def _read_environment(self):
        for e in os.environ:
            if e.startswith("CORE4_OPTION_"):
                value = os.environ[e]
                if e.find("__") >= 0:
                    (section, option) = e[len("CORE4_OPTION_"):].split(
                        "__")[0:2]
                else:
                    section = "DEFAULT"
                    option = e[len("CORE4_OPTION_"):]
                self._config.set(section, option, value)

    def _read_db(self):
        if self._db_conf is None:
            self._db_conf = {}
            coll = self.get_collection("sys.conf", "kernel")
            if coll:
                for doc in coll.find(sort=[("_id", 1)]):
                    if doc["_id"] not in self._db_conf:
                        self._db_conf[doc["_id"]] = {}
                    self._db_conf[doc["_id"]].update(doc["option"])
        if self._db_conf:
            self.config.read_dict(self._db_conf)

    @property
    def path(self):
        """
        Returns the processed local filenames. This attribute triggers
        lazy load of ``.config`` if not done, yet.

        :return: list of file locations
        """
        _ = self.config
        return self._path

    def __getattr__(self, item):
        """
        Delegates all methods and attributes to
        :class:`configparser.ConfigParser` object

        :param item: requested
        :return: value, raises ``AttributeError`` if not found
        """
        if item in self._WRAP:
            def section_wrapper(method):
                def config_wrapper(option, section=None, **kwargs):
                    return method(section or self.primary, option,
                                  **kwargs)

                return config_wrapper
            return section_wrapper(getattr(self.config, item))

        if item in self._FORWARD:
            return getattr(self.config, item)

        raise AttributeError

    def options(self, section=None):
        return self.config.options(section or self.primary)

    def has_section(self, section=None):
        return self.config.has_section(section or self.primary)

    def get_datetime(self, option, *args, **kwargs):
        """
        Parses the option into a :class:`~datetime.datetime` object using
        :mod:`dateutil.parser`. With this parser we are able to "read" the
        following example dates::

            2018-01-28
            2018-01-32
            2018 01 28 3:59
            2018-05-08T13:50:33
            20180128
            20180128111213
            2018.01.28 3:59
            2018/01/28 3:59

        :param option: string representing the option
        :return: :class:`datetime.datetime` object
        """
        value = self.get(option, *args, **kwargs)
        dt = dateutil.parser.parse(value, yearfirst=True)
        return dt

    def get_regex(self, option, *args, **kwargs):
        """
        parses regular expression using the slash delimiter as in
        ``/regex/mod`` where _regex_ represents the regular expression
        and _mod_ represents regular expression modifiers. Valid
        modifiers are the letters

        * ``i`` - for case-insensitive match
        * ``m`` - for multiple lines match
        * ``s`` - for dot matching newlines

        :return: compiled re object
        """
        regex = self.get(option, *args, **kwargs)
        return core4.util.parse_regex(regex)

    def get_collection(self, option, section=None):
        """
        parses an option into a :class:`.CoreCollection` object. The following
        option string format facilitates cross-database access patterns::

            [scheme://][username][:password]@[netloc]/[database]/[collection]

        The only mandatory part is the collection. The database name defaults to
        the scheme's default database option (``mongo_database``). The location
        and optional authentication data default to the scheme's default
        url option (``mongo_url``). Supported scheme is ``mongodb://``.

        This mechanic supports the following connection string examples::

            # fully qualified connection with location, database, collection

            mongodb://user:pass@localhost:27027/dbname/collname

            # default database with given scheme if exists, mongo_database
            # config option in this concrete example

            mongodb://user:pass@localhost:27027/collname

            # with default mongo_url using the passed authentication (user:pass)

            mongodb://user:pass@/dbname/collname

            # with default mongo_url, authentication and mongo_database

            mongodb://user:pass@/collname

            # use default mongo_url, including authentication, and
            # mongo_database to access collname

            mongodb://collname

        Raises ``ValueError`` if the option is malformed.

        :return: :class:`.CoreCollection` object
        """
        conn = self.config.get(section or self.primary, option)
        if not conn:
            return None
        split = urllib.parse.urlsplit(conn)
        opts = dict()
        opts["scheme"] = getattr(split, "scheme") or DEFAULT_SCHEME
        default_url = self.config.get(section or self.primary,
                                      SCHEME[opts["scheme"]]["url"])
        default_database = self.config.get(section or self.primary,
                                           SCHEME[opts["scheme"]]["database"])
        opts["username"] = split.username
        opts["password"] = split.password
        if split.hostname:
            (auth, *hostname) = split.netloc.split("@")
        else:
            default_split = urllib.parse.urlsplit(default_url)
            if not opts["username"] and not opts["password"]:
                opts["username"] = default_split.username
                opts["password"] = default_split.password
            (auth, *hostname) = default_split.netloc.split("@")
        if hostname:
            opts["hostname"] = hostname[0]
        else:
            opts["hostname"] = auth
        if not split.path:
            raise ValueError(
                "missing database/collection configuration with [{}]".format(
                    conn))
        (_db, *_coll) = [p for p in split.path.split("/") if p]
        if _db and _coll:
            opts["database"] = _db
            opts["collection"] = ".".join(_coll)
        else:
            opts["database"] = default_database
            opts["collection"] = _db
        return core4.base.collection.CoreCollection(**opts)
