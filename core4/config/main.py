# -*- coding: utf-8 -*-

import collections
import collections.abc
import os
import pprint

import pkg_resources
import yaml

import core4.base.collection
import core4.config.directive
import core4.config.map
from core4.error import Core4ConfigurationError
import core4.util

CONFIG_EXTENSION = ".yaml"
STANDARD_CONFIG = pkg_resources.resource_filename(
    "core4", "config/core" + CONFIG_EXTENSION)
USER_CONFIG = os.path.expanduser("core4/local" + CONFIG_EXTENSION)
SYSTEM_CONFIG = "/etc/core4/local" + CONFIG_EXTENSION
ENV_PREFIX = "CORE4_OPTION_"
DEFAULT = "DEFAULT"


class CoreConfig(collections.MutableMapping):
    """
    :class:`CoreConfig` is the gateway into core4 configuration. Please note
    that you normally do not instantiate this class yourself, since
    :class:`.CoreBase` carries a property ``.config`` which provides access to
    the context specific configuration cascade.
    """
    standard_config = STANDARD_CONFIG
    user_config = USER_CONFIG
    system_config = SYSTEM_CONFIG

    def __init__(self, extra_config=None, config_file=None):
        self._config_file = config_file
        self.extra_config = extra_config
        self.env_config = os.getenv("CORE4_CONFIG", None)
        self._config = None
        self.path = None

    @property
    def _c(self):
        self._load()
        return self._config

    def __getitem__(self, key):
        return self._c[key]

    def __setitem__(self, key, value):
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def __delitem__(self, key):
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def __iter__(self):
        return iter(self._c.items())

    def items(self):
        return collections.abc.ItemsView(self._c)

    def popitem(self):
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def values(self):
        return collections.abc.ValuesView(self._c)

    def keys(self):
        return self._c.keys()

    def __len__(self):
        return len(self._c)

    def _verify_dict(self, dct, msg):
        if not isinstance(dct, dict):
            raise Core4ConfigurationError(
                "expected dict with " + msg)

    def _parse(self, config, plugin=None, local=None):
        # collect standard config and standard DEFAULT
        standard_config = config.copy()
        self._verify_dict(standard_config, "standard config")
        standard_default = standard_config.pop(DEFAULT, {})
        self._verify_dict(standard_default, "standard DEFAULT")
        if local is not None:
            # collect local config and local DEFAULT
            local_config = local.copy()
            self._verify_dict(local_config, "local config")
            local_default = local_config.pop(DEFAULT, {})
            self._verify_dict(local_default, "local DEFAULT")
        else:
            local_config = {}
            local_default = {}
        # merge standard DEFAULT and local DEFAULT
        default = core4.util.dict_merge(standard_default, local_default)
        self._verify_dict(default, "DEFAULT")
        if plugin is not None:
            # collect plugin name, plugin config and plugin DEFAULT
            plugin_name = plugin[0]
            plugin_config = plugin[1]
            self._verify_dict(plugin_config, "plugin config")
            plugin_default = plugin_config.pop(DEFAULT, {})
            self._verify_dict(plugin_default, "plugin DEFAULT")
            # collection local plugin DEFAULT
            local_plugin_default = local_config.get(
                plugin_name, {}).pop(DEFAULT, {})
            self._verify_dict(local_plugin_default, "local plugin DEFAULT")
            # merge plugin DEFAULT and local plugin DEFAULT
            plugin_default = core4.util.dict_merge(
                plugin_default, local_plugin_default)
            # merge plugin config and standard config
            schema = core4.util.dict_merge(
                standard_config, {plugin_name: plugin_config})
        else:
            plugin_name = None
            plugin_default = {}
            schema = standard_config
        # merge config with local config
        result = core4.util.dict_merge(schema, local_config)
        # recursively forward DEFAULT into all dicts and into directives
        result = self._apply_default(result, default, plugin_name,
                                     plugin_default)
        # apply yaml tags
        self._apply_tags(result)
        # verify top level keys
        self._verify(result)
        # finalise the schema to cleanup local config with non existing keys
        schema = self._apply_default(schema, default, plugin_name,
                                     plugin_default)
        return self._cleanup(result, schema)

    def _verify(self, dct):
        """
        Confirm naming convention:

        # all top-level keys/options must not start with underscore (``_``)
        # all keys must not start with ``!`` except custom directives
        """
        for k in dct.keys():
            if k.startswith("_"):
                raise Core4ConfigurationError(
                    "top-level key/section "
                    "must not start with underscore [{}]".format(k))

        def traverse(d):
            for k, v in d.items():
                if k.startswith("!"):
                    if not ((k == "!connect") and (isinstance(v, str))):
                        raise Core4ConfigurationError(
                            "keys must not start with '!'")
                if isinstance(v, dict):
                    traverse(v)

        traverse(dct)

    def _cleanup(self, config, schema):
        def traverse(c, s, r):
            for k, v in c.items():
                if not isinstance(s, dict):
                    raise Core4ConfigurationError(
                        "invalid type cast [{}], expected dict".format(k))
                if k in s:
                    if isinstance(v, dict):
                        r[k] = {}
                        traverse(v, s[k], r[k])
                    else:
                        if not ((v is None) or (s[k] is None)):
                            if ((type(v) != type(s[k])
                                 and (not (type(v) in (int, float)
                                           and type(s[k]) in (int, float))))):
                                raise Core4ConfigurationError(
                                    "invalid type cast [{}] "
                                    "from [{}] to [{}]".format(
                                        k, type(s[k]).__name__,
                                        type(v).__name__))
                        r[k] = v

        ret = {}
        traverse(config, schema, ret)
        return ret

    def _apply_default(self, config, default, plugin_name=None,
                       plugin_default=None):

        def traverse(wlk, dflt, rslt):
            for k, v in dflt.items():
                rslt[k] = wlk.get(k, v)
            for k, v in wlk.items():
                if isinstance(v, dict):
                    rslt[k] = v.copy()
                    traverse(v, dflt, rslt[k])
                else:
                    rslt[k] = v

        # project plugin defaults
        if plugin_name is not None:
            temp = {}
            traverse(config[plugin_name], plugin_default, temp)
            config[plugin_name] = temp
        # project standard defaults
        temp = {}
        traverse(config, default, temp)
        return temp

    def _apply_tags(self, config):

        def traverse(config):
            for k, v in config.items():
                if isinstance(v, dict):
                    traverse(v)
                elif isinstance(v, core4.config.directive.ConnectTag):
                    v.set_config(config)

        traverse(config)

    def _load(self):
        """
        Internal method used to load configuration.
        """
        self._config = {}
        # standard config
        standard_data = self._read_yaml(self.standard_config)

        # extra config
        if self.extra_config and os.path.exists(self.extra_config[1]):
            extra = (self.extra_config[0],
                     self._read_yaml(self.extra_config[1]))
        else:
            extra = None

        # local config
        local_config = None
        if self._config_file:
            local_config = self._config_file
        elif self.env_config:
            local_config = self.env_config
        else:
            if self.user_config and os.path.exists(self.user_config):
                local_config = self.user_config
            else:
                if self.system_config and os.path.exists(self.system_config):
                    local_config = self.system_config
        if local_config:
            local_data = self._read_yaml(local_config)
        else:
            local_data = {}

        local_data = core4.util.dict_merge(
            local_data, self._read_db(standard_data, local_data))

        self._config.update(
            self._parse(standard_data, extra, local_data))

        self._read_env()

        self._config = core4.config.map.Map(self._config)
        return self._config

    def _read_yaml(self, filename):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                body = f.read()
            return yaml.safe_load(body) or {}
        else:
            raise FileNotFoundError(filename)

    def _read_db(self, standard_data, local_data):
        """
        Internal method used to parse all MongoDB document of the collection
        specified in ``config.sys.conf``.
        """
        opts = {}
        for attr in ("mongo_url", "mongo_database"):
            for config in (local_data, standard_data):
                for section in ("sys", DEFAULT):
                    data = config.get(section, {})
                    if attr in data:
                        opts[attr] = data[attr]
                        break  # the inner loop
                else:
                    continue  # if inner loop did not break
                break  # the outer loop if inner loop was broken
        local_sys = local_data.get("sys", {}).get("conf")
        standard_sys = standard_data.get("sys", {}).get("conf")
        connect = local_sys or standard_sys
        if connect:
            conf = {}
            coll = core4.config.directive.connect_mongodb(
                connect.conn_str, **opts)
            for doc in coll.find(projection={"_id": 0}, sort=[("_id", 1)]):
                conf = core4.util.dict_merge(conf, doc)
            return conf
        return {}

    def _read_env(self):
        pass

    # self._loaded = True
    #
    # # retrieve from cache
    # self.path = tuple(p[0] for p in proc)
    # if self.__class__._cache is not None:
    #     if self.path in self.__class__._cache:
    #         self._config = self.__class__._cache[self.path]
    #         self._debug("retrieve [{}] from cache", self.path)
    #         return self._config
    #
    # # load files
    # for path, add_key in proc:
    #     self._debug("parsing [{}]", path)
    #     self._read_file(path, add_keys=add_key)
    #
    # # load from sys.config
    # self._read_db()
    # # post process single OS environment variables
    # self._read_env()
    # # cascade top-level keys/values into other sections
    # self._cascade()
    # # recursively render and cleanse dict
    # self._config = self._explode(self._config)
    # # convert, cache and return
    # self._config = core4.config.map.Map(self._config)
    # self._debug("added {} at [{}]", self.path, id(self._config))
    # if self.__class__._cache is not None:
    #     self.__class__._cache[self.path] = self._config
    #
    # return self._config

    def __getattr__(self, item):
        return self._c[item]

    def __repr__(self):
        return pprint.pformat(self._c)

    # def _cascade(self):
    #     """
    #     Internal method used to cascade from top level configuration options
    #     and their values (default values) down into dictionaries encapsulating
    #     different configuration sections.
    #     """
    #     default = {}
    #     for k, v in self._config.items():
    #         if not isinstance(v, dict):
    #             default[k] = v
    #     for k, v in self._config.items():
    #         if isinstance(v, dict):
    #             self._debug("merging [{}]", k)
    #             self._config[k] = core4.util.dict_merge(
    #                 default, v)
    #
    # def _explode(self, dct, parent=None):
    #     """
    #     Internal method used to translate configuration statements into Python
    #     objects and to hide all callables from the parsed configuration file.
    #
    #     At the moment, the following extra statements are supported:
    #
    #     * :class:`core4.config.directive.connect`
    #     """
    #     if parent is None:
    #         parent = []
    #     dels = set()
    #     for k, v in dct.items():
    #         np = parent + [k]
    #         if isinstance(v, dict):
    #             self._debug("exploding [{}]", ".".join(np))
    #             self._explode(v, np)
    #         elif isinstance(v, core4.config.directive.connect):
    #             self._debug("connecting [{}]", ".".join(np))
    #             dct[k] = v.render(dct)
    #         elif callable(v):
    #             self._debug("removing [{}]", ".".join(np))
    #             dels.add(k)
    #     for k in dels:
    #         del dct[k]
    #     return dct

    # def _read_db(self):
    #     """
    #     Internal method used to parse all MongoDB document of the collection
    #     specified in ``config.sys.conf``.
    #     """
    #     conn = self._config["sys"]["conf"]
    #     if conn:
    #         coll = conn.render(self._config)
    #         conf = {}
    #         n = 0
    #         self._debug("retrieving configurations from [{}]", coll.info_url)
    #         for doc in coll.find(projection={"_id": 0}, sort=[("_id", 1)]):
    #             conf = core4.util.dict_merge(conf, doc)
    #             n += 1
    #         self._debug("retrieved [{}] configurations ", n)
    #         self._verify_key(conf)
    #         self._config = core4.util.dict_merge(
    #             self._config, conf, add_keys=False)
    #     return None
    #
    # def _read_env(self):
    #     """
    #     Internal method used to overwrite configuration options with values
    #     from OS environment variables.
    #     """
    #     for k, v in os.environ.items():
    #         if k.startswith(ENV_PREFIX):
    #             ref = self._config
    #             levels = k[len(ENV_PREFIX):].split("__")
    #             self._verify_key({levels[0]: v})
    #             for lev in levels[:-1]:
    #                 if lev in ref:
    #                     if not isinstance(
    #                             ref[lev], collections.MutableMapping):
    #                         ref[lev] = {}
    #                 else:
    #                     ref[lev] = {}
    #                 ref = ref[lev]
    #             if levels[-1] in ref:
    #                 old_val = ref[levels[-1]]
    #             else:
    #                 old_val = None
    #             if type(old_val) in (bool, int, float, str):
    #                 new_val = type(old_val)(v)
    #             else:
    #                 new_val = v
    #             if isinstance(new_val, str):
    #                 if new_val.strip() == "":
    #                     new_val = None
    #             self._debug("set [{}] = [{}] ({})", ".".join(levels), new_val,
    #                         type(new_val).__name__)
    #             ref[levels[-1]] = new_val
