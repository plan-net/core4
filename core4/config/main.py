import collections
import collections.abc
import os
import pprint

import dateutil.parser
import pkg_resources
import yaml
from datetime import datetime, date

import core4.base.collection
import core4.config.map
import core4.config.tag
import core4.util
from core4.error import Core4ConfigurationError

CONFIG_EXTENSION = ".yaml"
STANDARD_CONFIG = pkg_resources.resource_filename(
    "core4", "core4" + CONFIG_EXTENSION)
USER_CONFIG = os.path.expanduser("~/core4/local" + CONFIG_EXTENSION)
SYSTEM_CONFIG = "/etc/core4/local" + CONFIG_EXTENSION
ENV_PREFIX = "CORE4_OPTION_"
DEFAULT = "DEFAULT"


def parse_boolean(value):
    """
    Translates the passed value into a bool. If not pattern for ``True`` or
    ``False`` matches the passed value, then the actual value is returned.

    :param value: string representing ``True`` or ``False``
    :return: evaluated string as ``True`` or ``False`` or the original string
             value no pattern matches.
    """
    if value.lower() in ("yes", "y", "on", "1", "true", "t"):
        return True
    elif value.lower() in ("no", "n", "off", "0", "false", "f"):
        return False
    return value


def type_ident(a, b):
    """
    Internal helper method to verify that ``a`` and ``b`` are of the same type.
    If ``a`` or ``b`` is ``None``, this method returns ``True`` since the
    comparison is not possible.

    This method treats the following types as equal:

    * ``int`` and ``float``
    * ``datetime.datetime`` and ``datetime.date``, see :mod:`datetime`

    :return: `True` if ``a`` and ``b`` are considered equal, else ``False``
    """
    if ((type(a) != type(b))
            and (not ((type(a) in (int, float)
                       and type(b) in (int, float))
                      or (type(a) in (datetime, date)
                          and type(b) in (datetime, date))))):
        return False
    return True


class CoreConfig(collections.MutableMapping):
    """
    :class:`.CoreConfig` is the gateway into core4 configuration. Please note
    that you normally do not instantiate this class yourself, since
    :class:`.CoreBase` carries a property ``.config`` which provides access to
    the context specific configuration cascade.

    See :ref:`config` about core4 configuration principles.

    This class implements the delegation pattern and forwards all property
    access to configuration data stored in the ``._data`` attribute,
    accessible through :meth:`._config`. This attribute implements the
    :class:`.ConfigMap`.
    """
    cache = True
    standard_config = STANDARD_CONFIG
    user_config = USER_CONFIG
    system_config = SYSTEM_CONFIG

    _config_cache = None
    _file_cache = {}
    _db_cache = None

    def __init__(self, project_config=None, config_file=None, extra_dict={}):
        self._config_file = config_file
        self.project_config = project_config
        self.env_config = os.getenv("CORE4_CONFIG", None)
        self.extra_dict = extra_dict

    def __getitem__(self, key):
        """
        Delegates all property access to :meth:`._config`.
        """
        return self._config[key]

    def __setitem__(self, key, value):
        """
        Raises :class:`.Core4ConfigurationError` and implements
        a read-only configuration map with :class:`.ConfigMap`.
        """
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def __delitem__(self, key):
        """
        Read-only core4 configuration, see :meth:`__setitem__`
        """
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def __iter__(self):
        """
        Implements an iterator on :meth:`_config` items.
        """
        return iter(self._config.items())

    def __getattr__(self, item):
        """
        See :meth:`.__getitem__`.
        """
        return self._config[item]

    def __repr__(self):
        """
        :return: string representation of configuration data
        """
        return pprint.pformat(self._config)

    def __len__(self):
        """
        :return: length of configuration data
        """
        return len(self._config)

    def items(self):
        """
        :return: :class:`collections.abc.ItemsView` of configuration data
        """
        return collections.abc.ItemsView(self._config)

    def popitem(self):
        """
        Raises :class:`.Core4ConfigurationError` and implements
        a read-only configuration map with :class:`.ConfigMap`.
        """
        raise core4.error.Core4ConfigurationError(
            "core4.config.main.CoreConfig is readonly")

    def values(self):
        """
        :return: :class:`collections.abc.ValuesView` of configuration data
        """
        return collections.abc.ValuesView(self._config)

    def keys(self):
        """
        :return: keys of configuration data
        """
        return self._config.keys()

    @property
    def _config(self):
        """
        Loads and returns configuration data lazily.

        :return: :class:`.ConfigMap`
        """
        if self._config_cache is None:
            self._config_cache = self._load()
        return self._config_cache

    def _verify_dict(self, variable, message):
        """
        Verifies the passed variable is a Python dict. Raises
        :class:`.Core4ConfigurationError` if not.

        :param variable: to test if it is of type dict
        :param message: to raise if test failed
        """
        if not isinstance(variable, dict):
            raise Core4ConfigurationError(
                "expected dict with " + message)

    def _parse(self, config, project=None, local=None, extra=None):
        """
        Parses and merges the passed standard configuration, project
        configuration and local configuration sources.

        :param config: dict with standard configuration
        :param project: tuple with project name and project configuration dict
        :param local: dict with local configuration
        :param extra: dict with extra schema and default values
        :return: dict
        """
        # collect standard config and standard DEFAULT
        standard_config = config.copy()
        if extra:
            standard_config = core4.util.dict_merge(standard_config, extra)
        #self._verify_dict(standard_config, "standard config")
        standard_default = standard_config.pop(DEFAULT, {})
        self._verify_dict(standard_default, "standard DEFAULT")
        if local is not None:
            # collect local config and local DEFAULT
            local_config = local.copy()
            #self._verify_dict(local_config, "local config")
            local_default = local_config.pop(DEFAULT, {})
            self._verify_dict(local_default, "local DEFAULT")
        else:
            local_config = {}
            local_default = {}
        # merge standard DEFAULT and local DEFAULT
        default = core4.util.dict_merge(standard_default, local_default)
        #self._verify_dict(default, "DEFAULT")
        if project is not None:
            # collect project name, project config and project DEFAULT
            project_name = project[0]
            project_config = project[1].copy()
            #self._verify_dict(project_config, "project config")
            project_default = project_config.pop(DEFAULT, {})
            self._verify_dict(project_default, "project DEFAULT")
            # collect local project DEFAULT
            local_project_default = local_config.get(
                project_name, {}).pop(DEFAULT, {})
            self._verify_dict(local_project_default, "local project DEFAULT")
            # merge project DEFAULT and local project DEFAULT
            project_default = core4.util.dict_merge(
                project_default, local_project_default)
            # merge project config and standard config
            schema = core4.util.dict_merge(
                standard_config, {project_name: project_config})
        else:
            project_name = None
            project_default = {}
            schema = standard_config
        # merge config with local config
        result = core4.util.dict_merge(schema, local_config)
        # recursively forward DEFAULT into all dicts and into tags
        result = self._apply_default(result, default, project_name,
                                     project_default)
        # apply yaml tags
        self._apply_tags(result)
        # verify top level keys
        self._verify(result)
        # finalise the schema to cleanup local config with non existing keys
        schema = self._apply_default(schema, default, project_name,
                                     project_default)
        return self._apply_schema(result, schema)

    def _verify(self, dct):
        """
        Confirm naming convention:

        * all top-level keys/options must not start with underscore (``_``)
        """
        for k in dct.keys():
            if k.startswith("_"):
                raise Core4ConfigurationError(
                    "top-level key/section "
                    "must not start with underscore [{}]".format(k))

    def _apply_schema(self, config, schema):
        """
        Verifies that the top-level configuration variable is a Python
        dict and applies the passed schema: all configuration keys which do not
        exist in ``schema`` are silently ignored and not returned.

        Please note that the configuration key ``logging.extra`` is handled
        differently. This configuration key/value is forced to remain in the
        passed config.

        :param data: passed configuration data
        :param schema: configuration schema
        :return: updated configuration dict
        """
        def traverse(data, tmpl, result):
            if tmpl is None:
                return {}
            if not isinstance(tmpl, dict):
                raise Core4ConfigurationError(
                    "invalid type cast {}, expected dict".format(tmpl))
            for k, v in data.items():
                if k in tmpl:
                    if isinstance(v, dict):
                        result[k] = {}
                        traverse(v, tmpl[k], result[k])
                    else:
                        if not ((v is None) or (tmpl[k] is None)):
                            if not type_ident(v, tmpl[k]):
                                raise Core4ConfigurationError(
                                    "invalid type cast [{}] "
                                    "from [{}] to [{}]".format(
                                        k, type(tmpl[k]).__name__,
                                        type(v).__name__))
                        result[k] = v

        ret = {}
        traverse(config, schema, ret)
        # fix logging.extra schema constraints
        if "logging" in config and "extra" in config["logging"]:
            ret["logging"]["extra"] = config["logging"]["extra"]
        return ret

    def _apply_default(self, config, default, project_name=None,
                       project_default=None):
        """
        This method applies the passed standard ``default`` and project
        ``default``data to ``config``,

        Please note special handling of configuration key ``logging.extra``
        which is not processed by this method.

        :param config: dict of configuration data
        :param default: dict of standard default values
        :param project_name: string representing the project name and top-level
                            dictionary
        :param project_default: dict of project default values
        :return: updated dict of configuration data
        """

        def traverse(wlk, dflt, rslt):
            for k, v in dflt.items():
                rslt[k] = wlk.get(k, v)
            for k, v in wlk.items():
                if isinstance(v, dict):
                    rslt[k] = v.copy()
                    traverse(v, dflt, rslt[k])
                else:
                    rslt[k] = v

        # project project defaults
        if project_name is not None:
            temp = {}
            traverse(config[project_name], project_default, temp)
            config[project_name] = temp
        # project standard defaults
        temp = {}
        traverse(config, default, temp)
        # fix logging.extra schema constraints
        if "logging" in temp and "extra" in temp["logging"]:
            temp["logging"]["extra"] = config["logging"]["extra"]
        return temp

    def _apply_tags(self, config):
        """
        This method passes the configuration data to :class:`.ConnectTag`
        objects. These objects need the configuration settings to instantiate
        a :class:`.CoreCollection` object given their connection string and the
        default ``mongo_url`` and ``mongo_database``.

        :param config: dict
        """

        def traverse(dct):
            for k, v in dct.items():
                if isinstance(v, dict):
                    traverse(v)
                elif isinstance(v, core4.config.tag.ConnectTag):
                    v.set_config(dct)
        traverse(config)

    def _read_yaml(self, filename):
        """
        Parses the passed file.

        :param filename: to parse
        :return: YAML structure in Python dict format
        """
        if self.cache and filename in self.__class__._file_cache:
            body = self.__class__._file_cache[filename]
            return yaml.safe_load(body) or {}
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                body = f.read()
            if self.cache:
                self.__class__._file_cache[filename] = body
            data = yaml.safe_load(body) or {}
            self._verify_dict(data, filename)
            return data
        else:
            raise FileNotFoundError(filename)

    def _read_db(self, standard_data, local_data):
        """
        Parses all MongoDB document of collection specified in
        ``config.sys.conf``. The documents from ``sys.conf`` are read and
        parsed in alphabetic order. The last configuration key/value overwrites
        existing values.
        """
        if self._db_cache is not None:
            return self._db_cache
        # build OS environ lookup
        environ = {
            "DEFAULT": {},
            "sys": {}
        }
        for k in ("DEFAULT", "sys"):
            for opt in ("mongo_url", "mongo_database"):
                os_key = "{}{}__{}".format(ENV_PREFIX, k, opt)
                if os_key in os.environ:
                    environ[k][opt] = os.getenv(os_key)
        # make defaults for mongo_url and mongo_database
        opts = {}
        for attr in ("mongo_url", "mongo_database"):
            for config in (environ, local_data, standard_data):
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
        env_sys = os.getenv("CORE4_OPTION_sys__conf")

        connect = local_sys or standard_sys
        if connect or env_sys:
            if env_sys:
                conn_str = env_sys[len("!connect "):]
            else:
                conn_str = connect.conn_str
            conf = {}
            coll = core4.config.tag.connect_database(
                conn_str, **opts)
            for doc in coll.find(projection={"_id": 0}, sort=[("_id", 1)]):
                conf = core4.util.dict_merge(conf, doc)
            self._db_cache = self._resolve_tags(conf)
        else:
            self._db_cache = {}
        return self._db_cache

    def _read_env(self):
        """
        Overwrite configuration options with values from OS environment
        variables.
        """
        env = {}
        for k, v in os.environ.items():
            if k.startswith(ENV_PREFIX):
                levels = k[len(ENV_PREFIX):].split("__")
                ref = env
                if v.strip() == "~":
                    v = None
                for lev in levels[:-1]:
                    if lev not in ref:
                        ref[lev] = {}
                    ref = ref[lev]
                ref[levels[-1]] = self._env_convert(v)
        return self._resolve_tags(env)

    def _resolve_tags(self, config):
        """
        This method implements the ``!connect`` tag for core4 environment
        variables and documents from ``sys.conf``.

        :param config: current config data before custom tag processing
        :return: updated config dict
        """

        def traverse(dct, update):
            for k, v in dct.items():
                update[k] = {}
                if isinstance(v, dict):
                    traverse(v, update[k])
                    continue
                elif isinstance(v, str):
                    if v.startswith("!connect "):
                        tag = core4.config.tag.ConnectTag(
                            v[len("!connect "):])
                        # tag.set_config(dct)
                        v = tag
                update[k] = v

        temp = {}
        traverse(config, temp)
        return temp

    def _env_convert(self, value):
        """
        Converts the following type tags when parsing environment variables:

        * ``!!bool``
        * ``!!float``
        * ``!!int``
        * ``!!str``
        * ``!!timestamp``

        The tag ``!!timestamp`` uses :mod:`python-dateutil` to parse date/time
        strings.

        :param value: to parse
        :return: parsed value if any of the listed tags applies, else the
                 original value is returned
        """
        if value is None:
            return None
        converter = {
            "!!bool": lambda r: parse_boolean(r),
            "!!float": lambda r: float(r),
            "!!int": lambda r: int(r),
            "!!str": lambda r: str(r),
            "!!timestamp": lambda r: dateutil.parser.parse(r)
            ,
        }
        for typ, conv in converter.items():
            if value.startswith(typ + " "):
                upd = value[len(typ) + 1:]
                return conv(upd)
        return value

    def _load(self):
        """
        Loads the configuration from

        #. core4 standard configuration file
        #. project configuration file
        #. local configuration defined in environment variable
           ``CORE4_CONFIG``, in user's home, or the system folder
           ``/etc/core``
        #. MongoDB collection ``sys.conf``
        #. environment variables

        :return: :class:`.ConfigMap`
        """
        # extra config
        if self.project_config and os.path.exists(self.project_config[1]):
            lookup = self.project_config[0]
        else:
            extra = lookup = None

        if lookup is not None:
            extra_config = self._read_yaml(self.project_config[1])
            extra = (lookup, extra_config)

        # standard config
        standard_data = self._read_yaml(self.standard_config)

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

        # read OS environment variables
        environ = self._read_env()

        # merge sys.conf
        local_data = core4.util.dict_merge(
            local_data, self._read_db(standard_data, local_data))

        local_data = core4.util.dict_merge(local_data, environ)

        # merge OS environ
        data = core4.config.map.ConfigMap(
            self._parse(standard_data, extra, local_data, self.extra_dict)
        )
        return data
