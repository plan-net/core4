configuration management
========================

All core4 components have access to core4 configuraiton management with
class :class:`.CoreConfig` in :mod:`core4.config.main`.


configuration principles
------------------------

core4 configuration is considered a key feature of the framework. System
configuration of all shape are the bridge between development and
operations activities. The :mod:`core4.config` package primary concerns are:

#. To keep sensitive data safe and keep naive staff and smart hackers out.
#. To make the life of system administrators easy. The config system supports
   various configuration sources, e.g. a ``local.conf`` file , a central mongodb
   ``sys.conf`` collection, user configuration files, default values, OS
   environment variables as well as plugin specific config files. Administrators
   choose their weapons.
#. To make the life of data scientists and developers easy. The config system
   supports cross-database application development, local and remote sources,
   and a hierarchical connection configuration mechanic which speed up the most
   critical ingridient to efficient programming: access to real data.


sources of configuration
------------------------

There are six places where core4 is looking for configuration sections
and their options. Environment variables prefixed with ``CORE4_OPTION_``
take precedence over the following core4 configuration source:

#. the default configuration in ``config/conf.yaml``
#. the plugin configuration for plugin specific settings in
   ``[PLUGIN]/[PLUGIN].yaml``
#. a local configuration located by the environment variable ``CORE4_CONFIG``
#. the user specific configuration in his or her home ``~/core4/local.yaml``
#. the system wide local configuration in ``/etc/core4/local.yaml``

Option 3 takes precedence over option 4 which takes precedence over option 5.

This boils down into the following tactic:

* Default values are set in ``/config/core.yaml``. These should not be change by
  your setup.
* Plugin specific variables and values are set in the plugin configuration file.
  For each plugin exists one and only one plugin specific configuration file.
* A local configuration file can always be enforced with the ``CORE4_CONFIG``
  environment variables.
* A user-specific configuration file located at ``~/core4/local.yaml`` takes
  precedence over a system-specific configuration file located at
  ``/etc/core4/local.yaml``.
* If ``sys.conf`` is defined in section ``[kernel]`` then a central MongoDB
  collection is merged.
* Finally the user always has the chance to enforce individual
  configuration option values with environment variables of the operating
  system.

The next section explains the structure of OS environment configuration options
and their values.


configuration structure
-----------------------

:class:`.CoreConfig` uses :class:`~configparser.ConfigParser` of the Python
standard library. It supports the `INI file structure`_ as well as a YAML file
structure depending on the file extension ``.ini``, ``.conf``, ``.yml`` and
``.yaml``.


environment options and values
------------------------------

You can enforce core configuration option values by defining operating
system variables. The structure of these environment variables is::

    CORE4_OPTION_[section]__[option]
    CORE4_OPTION_[option]

Please note the **double** underscore characters separating the configuration
section from the option. If no section is provided as in the second example,
then the ``DEFAULT`` section applies.


option types
------------

Access to configuration options is provided with
:class:`~configparser.ConfigParser` standard methods:

* :meth:`~configparser.ConfigParser.get`
* :meth:`~configparser.ConfigParser.getint`
* :meth:`~configparser.ConfigParser.getfloat`
* :meth:`~configparser.ConfigParser.getboolean`

:class:`.CoreConfig` delegates these methods to
:class:`~configparser.ConfigParser`. :class:`.CoreConfig` adds the following
extra access methods:

* :meth:`~.CoreConfig.get_datetime` - returns a :class:`datetime.datetime`
  object
* :meth:`~.CoreConfig.get_regex` - returns a `Python regular expression object`_
* :meth:`~.CoreConfig.get_collection` - returns :class:`.CoreCollection` object

:class:`.CoreConfig` delegates the following methods to the
:class:`~configparser.ConfigParser` object.

* :meth:`~configparser.ConfigParser.has_section`
* :meth:`~configparser.ConfigParser.has_option`
* :meth:`~configparser.ConfigParser.sections`
* :meth:`~configparser.ConfigParser.defaults`
* :meth:`~configparser.ConfigParser.options`

.. _primary_section:

primary section
---------------

Each :class:`.CoreConfig` object has a primary section. This section is queried
with the methods described above if no explicit section is specified. The
default primary section is ``DEFAULT``.


.. _INI file structure: https://python.readthedocs.io/en/latest/library/configparser.html#supported-ini-file-structure
.. _Python regular expression object: https://docs.python.org/3/library/re.html#re-objects
