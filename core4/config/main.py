# -*- coding: utf-8 -*-

import configparser
import os

import dateutil.parser
import pkg_resources

# todo: implement special getters

# config locations, see https://pypi.org/project/appdirs/1.4.0/
EXTENDED_INTERPOLATION = False
LOCAL_USER_CONFIG = os.path.expanduser('core4/local.conf')
DEFAULT_CONFIG = pkg_resources.resource_filename('core4', 'config/core.conf')
SYSTEM_CONFIG = '/etc/core4'


class CoreConfig:
    """
    The CoreConfig class is the gateway into core4 configuration. It is
    implemented as a proxy into configparser.ConfigParser() with a
    defined set of configuration sources and the concept of a primary
    section.

    The proxy object

    # forward methods .defaults() and .sections()
    # wrap methods .add_section(), .options(), .get(), .getint(),
      .getfloat(), .getboolean(), .items(), .has_option(), .set() with
      the primary section
    # hide methods .read(), .read_file(), .read_string(), .read_dict(),
      .popitem(), .optionxform(), .write(), .remove_option(),
      .remove_section()

    By default the config object uses BasicInterpolation. You can change this
    behavior to ExtendedInterpolation with the extended parameter.
    """

    _WRAP = ['has_section', 'options', 'get', 'getint', 'getfloat',
             'getboolean', 'has_option']
    _FORWARD = ['defaults', 'sections']

    default_config = DEFAULT_CONFIG
    user_config = LOCAL_USER_CONFIG
    system_config = SYSTEM_CONFIG

    _cache = {}

    def __init__(self, section='DEFAULT', extra_config=None, config_file=None,
                 extended=EXTENDED_INTERPOLATION):
        self._config_file = config_file
        self.extra_config = extra_config
        self.primary = section
        self.env_config = os.getenv('CORE4_CONFIG', None)
        self._extended = extended
        self._config = None
        self._path = []

    @classmethod
    def purge_cache(cls):
        """
        purges and class-level cache
        """
        cls._cache = {}

    @property
    def config(self):
        """
            provides lazy access to configparser ConfigParser object loaded from

            #. core's **default** configuration file (./core4/config/core.conf)
            #. an **extra** configuration file (defaults to None)
            #. a **local** configuration file (by OS environment variable
               ``CORE4_CONFIG``, or in the user's home directory
               ``~/.core/local.conf``, or in the system directory
               ``/etc/core/local.conf``, or in collection ``core4.sys.config``.
               The first existing config provider wins and local configuration
               processing stops.
            #. OS environment variables following the naming convention
               ``CORE4_[SECTION]__[OPTION]`` (watch the double underscore
               between section and option) are applied as the final step to
               load core4 configuration.

            :return: configparser.ConfigParser object
        """
        if self._config is None:
            # extra_config only drives the caching
            cache_item = str(self.extra_config)
            if cache_item in self.__class__._cache:
                return self.__class__._cache[cache_item]
            if self._extended:
                self._config = configparser.ConfigParser(
                    interpolation=configparser.ExtendedInterpolation())
            else:
                self._config = configparser.ConfigParser()
            # step #1: core configuration
            self._read_file(self.default_config)
            # step #2: extra configuration
            if self.extra_config:
                self._read_file(self.extra_config)
            # step #3: local configuration
            if self._config_file:
                self._read_file(self._config_file)
                pass
            elif self.env_config:
                # by OS environment variable CORE_CONFIG
                if os.path.exists(self.env_config):
                    self._read_file(self.env_config)
            elif os.path.exists(self.user_config):
                # in user's home directory ~/
                self._read_file(self.user_config)
            elif os.path.exists(self.system_config):
                # in system configuration directory /etc
                self._read_file(self.system_config)
            # in core4 system collection sys.config
            self._read_db()
            # post process single OS environment variables
            self._read_environment()
            self.__class__._cache[cache_item] = self._config
        return self._config

    def _read_file(self, filename):
        if os.path.exists(filename):
            self._config.read(filename)
            self._path.append(filename)
        else:
            raise FileNotFoundError(filename)

    def _read_environment(self):
        for e in os.environ:
            if e.startswith('CORE4_OPTION_'):
                value = os.environ[e]
                if e.find('__') >= 0:
                    (section, option) = e[len('CORE4_OPTION_'):].split(
                        '__')[0:2]
                else:
                    section = 'DEFAULT'
                    option = e[len('CORE4_OPTION_'):]
                self._config.set(section, option, value)

    def _read_db(self):
        # todo: requires implementation
        pass

    @property
    def path(self):
        """
        This method triggers lazy load of ``.config`` and returns the processed
        local filenames.

        :return: list of file locations
        """
        _ = self.config
        return self._path

    def __getattr__(self, item):
        """
        Delegates all methods and attributes to configparser.ConfigParser object
        at self.config.

        :param item: requested
        :return: value, raises AttributeError if not found
        """

        # wrap methods has_section (1), options (1), get (2: section,
        #   option), dito getint, getfloat, getboolean, has_option
        # forward methods: defaults, sections

        if item in self._WRAP:

            def mywrapper(method):
                def methodWrapper(option, *, section=None, **kwargs):
                    return method(section or self.primary, option, **kwargs)
                return methodWrapper

            return mywrapper(getattr(self.config, item))

        if item in self._FORWARD:
            return getattr(self.config, item)

        raise AttributeError

    def get_datetime(self, option, *args, **kwargs):
        """
        Parses the option into a ``datetime`` object using dateutil.parser.
        With this datetime parser we are able to "read" the following example
        dates:

        * 2018-01-28
        * 2018-01-32
        * 2018 01 28 3:59
        * 2018-05-08T13:50:33
        * 20180128
        * 20180128111213
        * 2018.01.28 3:59
        * 2018/01/28 3:59

        :param option: string representing the option
        :param *args: further args to be passed to .get()
        :return: datetime object
        """

        value = self.get(option, *args, **kwargs)
        dt = dateutil.parser.parse(value, yearfirst=True)
        return dt

    def get_regex(self, option, *args, **kwargs):
        """
        parses regular expression using the slash delimiter as in ``/regex/mod``
        where _regex_ represents the regular expression and _mod_ represents
        regular expression modifiers. Valid modifiers are the letters

        * ``i`` - for case-insensitive match
        * ``m`` - for multiple lines match
        * ``s`` - for dot matching newlines

        :return: re object
        """
        value = self.get(option, *args, **kwargs)
        return value

    # def get_collection(self):
    #     """
    #     parses a MongoDB connection string into connection settings
    #
    #     :return: dict
    #     """
    #     pass
