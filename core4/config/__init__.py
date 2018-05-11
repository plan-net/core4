# -*- coding: utf-8 -*-

"""
core4 configuration management
==============================

All core4 components have access to core4 configuraiton management with
class CoreConfig in core4.config.main.


configuration principles
========================

core4 configuration is considered a key feature of the framework. System
configuration of all shape are the bridge between development and
operations activities. The core4.config package primary concerns are:

#. To keep sensitive data safe and keep naive staff and smart hackers
   out,
#. To make the lifes of system administrators easy. The config system
   supports various configuration sources, e.g. ``local.conf``, a
   central mongodb ``sys.conf`` collection, user configuration files,
   default values, OS environment variables as well as plugin specific
   config files. Administrators choose their weapons.
#. To make the lifes of data scientists and developers easy. The config
   system supports cross-database application development, local and
   remote sources, and a hierarchical connection configuration mechanic
   which speeds up the most critical ingridient to efficient
   programming: access to real data.


sources of configuration
------------------------

There are six places where core4 is looking for configuration sections
and their options. Environment variables prefixed with ``CORE4_OPTION_``
take precedence over the following core4 configuration source:

#. the default configuration in ``config/conf.core``
#. the plugin configuration for plugin specific settings in
   ``PLUGIN/PLUGIN.conf``
#. a local configuration located by the environment variable
   ``CORE4_CONFIG``
#. the user specific configuration in ``~/core4/local.conf``
#. the system wide local configuration in ``/etc/core4/local.conf``

Option 3 takes precedence over option 4 which takes precedence over
option 5.

This boils down into the following tactic:

* default values are set in ``/config/core.conf``. These should not
  be change by your setup.
* plugin specific variables and values are set in the plugin
  configuration file
* for each plugin exists one and only one plugin specific configuration
  file
* a local configuration file can always be enforced with the
  ``CORE4_CONFIG`` environment variables
* a user-specific configuration file located at ``~/core4/local.conf``
  takes precedence over a system-specific configuration file located at
  ``/etc/core4/local.conf``
* if ``sys.conf`` is defined in section [kernel] then a central MongoDB
  collection is merged
* finally the user always has the chance to enforce individual
  configuration option values

The next section explains the structure of environment configuration
options and their values.


environment options and values
------------------------------

You can enforce core configuration option values by defining operating
system variables. The structure of these environment variables is::

    CORE4_OPTION_[section]__[option]

or::

    CORE4_OPTION_[option]

Please note the **double** underscore characters seperating the
configuration section from the option. If no section is provided as in
the second example, then the ``DEFAULT`` section applies.


option types
------------

Access to configuration options is provided with configparser standard
methods:

* .get(option, section=None)
* .getint(option, section=None)
* .getfloat(option, section=None)
* .getboolean(option, section=None)

CoreConfig class adds the following extra access methods:

* .get_datetime(option, section=None) - returns datetime.datetime
* .get_regex(option, section=None) - return re object
* .get_collection(option, section=None) - returns CoreCollection

CoreConfig delegates the following methods to the internal ConfigParser
object, with section default to primary section of the config. For
further details of the core :class:`.Config` class:

* .has_section(section=None)
* .has_option(section=None)
* .sections()
* .defaults()
* .options(section=None)
"""

from core4.config.main import CoreConfig
