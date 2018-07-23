# -*- coding: utf-8 -*-

import collections
import os
import pprint

import pkg_resources

import core4.base.collection
import core4.error
import core4.util
from core4.base.collection import SCHEME

CONFIG_EXTENSION = ".py"
DEFAULT_CONFIG = pkg_resources.resource_filename("core4", "config/core"
                                                 + CONFIG_EXTENSION)
USER_CONFIG = os.path.expanduser("core4/local" + CONFIG_EXTENSION)
SYSTEM_CONFIG = "/etc/core4/local" + CONFIG_EXTENSION
ENV_PREFIX = "CORE4_OPTION_"


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


class Map(dict):
    """
    a dictionary that supports dot notation
    as well as dictionary access notation
    usage: d = DotDict() or d = DotDict({'val1':'first'})
    set attributes: d.val2 = 'second' or d['val2'] = 'second'
    get attributes: d.val2 or d['val2']
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if isinstance(value, collections.MutableMapping):
                value = Map(value)
            self[key] = value


class CoreConfig(collections.MutableMapping):
    default_config = DEFAULT_CONFIG
    user_config = USER_CONFIG
    system_config = SYSTEM_CONFIG
    _db_conn = None
    _cache = {}

    def __init__(self, section="DEFAULT", extra_config=None, config_file=None):
        self._config_file = config_file
        self.extra_config = extra_config
        self.section = section
        self.env_config = os.getenv("CORE4_CONFIG", None)
        self._config = None
        self._loaded = False
        self.path = None
        self._trace = []

    def _debug(self, str, *args, **kwargs):
        msg = "{}: ".format(id(self)) + str.format(*args, **kwargs)
        self._trace.append(msg)

    @property
    def trace(self):
        return "\n".join(self._trace)

    def __getitem__(self, key):
        self._load()
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value

    def __delitem__(self, key):
        del self._config[key]

    def __iter__(self):
        self._load()
        return iter(self._config)

    def __len__(self):
        self._load()
        return len(self._config)

    def _load(self):
        if self._loaded:
            self._debug("retrieve [{}] from memory at [{}]", self.path,
                        id(self._config))
            return

        self._config = {}
        # collect configuration files
        proc = []
        # step #1: core configuration
        proc.append((self.default_config, True))
        # step #2: extra configuration
        if self.extra_config and os.path.exists(self.extra_config):
            proc.append((self.extra_config, True))
        # step #3: enfoced local configuration
        if self._config_file:
            proc.append((self._config_file, False))
        # by OS environment variable CORE_CONFIG
        elif self.env_config:
            proc.append((self.env_config, False))
        else:
            if self.user_config and os.path.exists(self.user_config):
                # in user's home directory ~/
                proc.append((self.user_config, False))
            else:
                if self.system_config and os.path.exists(self.system_config):
                    proc.append((self.system_config, False))

        self._loaded = True

        # retrieve from cache
        self.path = tuple(p[0] for p in proc)
        if self.__class__._cache is not None:
            if self.path in self.__class__._cache:
                self._config = self.__class__._cache[self.path]
                self._debug("retrieve [{}] from cache", self.path)
                return self._config

        # load files
        for path, add_key in proc:
            self._debug("parsing [{}]", path)
            self._read_file(path, add_keys=add_key)

        # load from sys.config
        self._read_db()
        # post process single OS environment variables
        self._read_env()
        # cascade top-level keys/values into other sections
        self._cascade()
        # recursively render and cleanse dict
        self._config = self._explode(self._config)
        # convert, cache and return
        self._config = Map(self._config)
        self._debug("added {} at [{}]", self.path, id(self._config))
        if self.__class__._cache is not None:
            self.__class__._cache[self.path] = self._config

        return self._config

    def __getattr__(self, item):
        self._load()
        return self._config[item]

    def __repr__(self):
        self._load()
        return pprint.pformat(self._config)

    def _cascade(self):
        default = {}
        for k, v in self._config.items():
            if not isinstance(v, dict):
                default[k] = v
        for k, v in self._config.items():
            if isinstance(v, dict):
                self._debug("merging [{}]", k)
                self._config[k] = core4.util.dict_merge(
                    default, v)

    def _explode(self, dct, parent=None):
        if parent is None:
            parent = []
        dels = set()
        for k, v in dct.items():
            np = parent + [k]
            if isinstance(v, dict):
                self._debug("exploding [{}]", ".".join(np))
                self._explode(v, np)
            elif isinstance(v, connect):
                self._debug("connecting [{}]", ".".join(np))
                dct[k] = v.render(dct)
            elif callable(v):
                self._debug("removing [{}]", ".".join(np))
                dels.add(k)
        for k in dels:
            del dct[k]
        return dct

    def _verify_key(self, dct):
        for k in dct.keys():
            if k.startswith("_"):
                raise core4.error.Core4ConfigurationError(
                    "top-level key/section "
                    "must not start with underscore [{}]".format(k))
            elif k == "trace":
                raise core4.error.Core4ConfigurationError(
                    "reserved top-level key/section [{}]".format(k))


    def _read_file(self, filename, add_keys=False):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                body = f.read()
            gns = {}
            lns = {}
            exec(body, gns, lns)
            self._verify_key(lns)
            self._config = core4.util.dict_merge(
                self._config, lns, add_keys)
        else:
            raise FileNotFoundError(filename)

    def _read_db(self):
        conn = self._config["kernel"]["sys.conf"]
        if conn:
            coll = conn.render(self._config)
            conf = {}
            n = 0
            self._debug("retrieving configurations from [{}]", coll.info_url)
            for doc in coll.find(projection={"_id": 0}, sort=[("_id", 1)]):
                conf = core4.util.dict_merge(conf, doc)
                n += 1
            self._debug("retrieved [{}] configurations ", n)
            self._verify_key(conf)
            self._config = core4.util.dict_merge(
                self._config, conf, add_keys=False)
        return None

    def _read_env(self):
        for k, v in os.environ.items():
            if k.startswith(ENV_PREFIX):
                ref = self._config
                levels = k[len(ENV_PREFIX):].split("__")
                self._verify_key({levels[0]: v})
                for lev in levels[:-1]:
                    if lev in ref:
                        if not isinstance(ref[lev], collections.MutableMapping):
                            ref[lev] = {}
                    else:
                        ref[lev] = {}
                    ref = ref[lev]
                if levels[-1] in ref:
                    old_val = ref[levels[-1]]
                else:
                    old_val = None
                if type(old_val) in (bool, int, float, str):
                    new_val = type(old_val)(v)
                else:
                    new_val = v
                if isinstance(new_val, str):
                    if new_val.strip() == "":
                        new_val = None
                self._debug("set [{}] = [{}] ({})", ".".join(levels), new_val,
                            type(new_val).__name__)
                ref[levels[-1]] = new_val
