import configparser
import os

# todo: check if we want ExtendedInterpolation

class CoreConfig():
    
    """
    The CoreConfig class is the gateway into core4 configuration.
    """

    def __init__(self, section='DEFAULT', extra_config=None, *args, **kwargs):
        self.default_config = None
        self.env_config = os.getenv('CORE_CONFIG', None)
        self.user_config = None
        self.system_config = None
        self.extra_config = None
        self._config = None

    @property
    def config(self):
        """
            provides lazy access to configparser ConfigParser object loaded from

            #. core's **default** configuration file (./core4/config/core.conf)
            #. an **extra** configuration file (defaults to None)
            #. a **local** configuration file (by OS environment variable
               ``CORE_CONFIG``, or in the user's home directory
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
            self._config = configparser.ConfigParser()
            # step #1: core configuration
            self._read_file(self.core_config)
            # step #2: extra configuration
            if self.extra_conf:
                self._read_file(self.extra_conf)
            # step #3: local configuration
            if self.env_config:
                # by OS environment variable CORE_CONFIG
                if os.path.exists(self.env_config):
                    self._read_file(self.env_config)
            elif os.path.exists(self.user_config):
                # in user's home directory ~/
                self._read_file(self.user_config)
            elif os.path.exists(self.system_config):
                # in system configuration directory /etc
                self._read_file(self.system_config)
            else:
                # in core4 system collection sys.config
                self._read_db()
            # post process single OS environment variables
            self._read_environment()
        return self._config

    @property
    def path(self):
        """
        This method triggers lazy load of ``.config`` and returns the processed
        local filenames.
        
        :return: list of file locations
        """
        pass
    
    def _read_file(self, filename):
        pass

    def _read_db(self):
        pass

    def _read_environment(self):
        pass

    def get_datetime(self):
        """
        parses date/time as defined by DEFAULT.datetime_long_format or
        DEFAULT.datetime_short_format

        :return: datetime.datetime object
        """
        pass

    def get_date(self):
        """
        parses date as defined by DEFAULT.date_format

        :return: datetime.datetime object
        """
        pass

    def get_time(self):
        """
        parses time as defined by DEFAULT.time_long_format or
        DEFAULT.time_short_format

        :return: datetime.time object
        """
        pass

    def get_regex(self):
        """
        parses regular expression using the slash delimiter as in ``/regex/mod``
        where _regex_ represents the regular expression and _mod_ represents
        regular expression modifiers. Valid modifiers are the letters
        
        * ``i`` - for case-insensitive match
        * ``m`` - for multiple lines match
        * ``s`` - for dot matching newlines
        
        :return: re object
        """
        pass

    def get_collection(self):
        """
        parses a MongoDB connection string into connection settings
        
        :return: dict
        """
        pass

    def __getattr__(self, item):
        # delegate methods to self.config
        pass
