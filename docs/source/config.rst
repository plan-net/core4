configuration
=============

All core4 components based on :class:`.CoreBase` have access to core4
configuraiton management with class :class:`.CoreConfig` in
:mod:`core4.config.main`.


configuration principles
------------------------

core4 configuration is considered a key feature of the framework. System
configuration of various kind are the bridge between development and
operations activities. The key elements are:

#. to keep sensitive data safe and keep naive staff and smart hackers out.
#. to make the life of system administrators easy. The config system supports
   various configuration sources, e.g. configuration files, a central mongodb
   ``sys.conf`` collection, user configuration files, default values, OS
   environment variables as well as plugin specific config files.
   Administrators choose their weapons.
#. to make the life of data scientists and developers easy. The config system
   supports cross-database application development, local and remote sources,
   and a hierarchical connection configuration mechanic which speed up the most
   critical ingridient to efficient programming: data access.

core4 configuration format is pure Python code. The discussion about the pros
and cons of the various configuration formats can be found all over the place
(see for example `Python as configuration files`_ and especially
`Matteo's comment`_).

The following arguments led us to chose Python as the configuration format:

* Python is easy.
* We do not consider Python code a security thread because if a user can modify
  a configuration file he/she can already do whatever the application can do.
* To follow a declarative or procedural structure of the configuration is left
  to the programmer and operator.


sources of configuration
------------------------

There are six places where core4 is looking for configuration sections
and their options. Environment variables prefixed with ``CORE4_OPTION_``
take precedence over the following core4 configuration sources:

#. the default configuration in ``config/core.py``
#. the plugin configuration for plugin specific settings in
   ``[PLUGIN]/[PLUGIN].py``. This plugin configuration is part of the plugin
   repository and is considered to provide plugin specific default values.
#. a local configuration located by the environment variable ``CORE4_CONFIG``
#. the user specific configuration in his or her home ``~/core4/local.py``
#. the system wide local configuration in ``/etc/core4/local.py``
#. the central configuration database collection ``sys.conf``

Option 3 takes precedence over option 4 which takes precedence over option 5.
Option 6 is applied, if ``sys.conf`` is not ``None``.

This boils down to the configuration flow outlined in the following diagram:

.. figure:: _static/config.png
   :scale: 100 %
   :alt: configuration flow

Default values are set in ``core.py``. Plugin specific variables and values are
set in the plugin configuratio file. For each plugin exists one and only one
plugin specific configuration file. A local configuration file can be enforced
with the ``CORE4_CONFIG`` environment variables. If ``CORE4_CONFIG`` is
defined, then the processing of the user configuration file and the system
configuration file is skipped. If ``CORE4_CONFIG`` is not defined, then the
system joins the user configuration file if it exists. If no user configuration
file exists, then the system configuration file is joined if it exists. If the
MongoDB collection ``sys.conf`` is defined, then all options and their values
are joined. Finally all configuration options from the operating system
environment variables overwrite existing values (see :ref:`env_config`).

.. important:: **Outer versus inner configuration join**. The core4 default
               configuration and additionally for plugin classes the plugin
               configuration options define the scope of configuration options
               (**outer join** statement in the diagram). All settings in the
               other configuration sources (``CORE4_CONFIG``, user
               configuration, system configuration, ``sys.conf`` and OS
               environment variables) which are not in this scope scope are
               ignored (**inner join** statement in the diagram).


configuration structure
-----------------------

core4 configuration is implemented with pure Python code and the configuration
is evaluated at runtime. This applies to all file based configuration sources.
It does not apply to MongoDB collection ``sys.conf``. All fields of all
documents of collection ``sys.conf`` overwrite existing configuration
settings with their values. Non-existing fields are ignored.

.. note:: The documents in ``sys.conf`` are processed in alphabetical order.

The configuration is to be structured in sections. Top level dict variables
represent sections. The ``logging`` dict in the default configuration file
``core.py`` is such a section::

    logging = {
        "stderr": "DEBUG",
        "stdout": None,
        "mongodb": "INFO",
        "format": "%(asctime)s "
                  "- %(levelname)-8s "
                  "[%(qual_name)s/%(identifier)s] "
                  "%(message)s",
        "exception": {
            "capacity": 1000
        },
        "extra": None
    }


In contrast to Python dictionaries all top-level primitive variables represent
default values. Variables with primitive data type are copied to all sections
if not defined in the section dictionary and therefore represent default
values. The following configuration example demonstrates this behavior::

    my_value = 123

    sect1 = {
        "my_string": "hello world"
    }

    sect2 = {
        "my_value": 456
    }

Configuration access snippt::

    >>> import core4.base

    >>> example = core4.base.CoreBase()
    >>> print(example.config.my_value)
    123

    >>> print(example.config.sect1.my_string)
    "hello world"

    >>> print(example.config.sect1.my_value)
    123

    >>> print(example.config.sect2.my_value)
    456


.. _env_config:

environment options and values
------------------------------

The developer/operator can enforce core configuration option values by defining
operating system variables. The structure of these environment variables is::

    CORE4_OPTION_[section]__[option]
    CORE4_OPTION_[option]

Please note the **double** underscore characters separating the configuration
section from the option. If no section is provided as in the second example,
then the top section applies.


configuration access
--------------------

All classes based on :class:`.CoreBase` have configuration access via the
``self.config`` attribute. To access configuration options and values you can
either use plain dictionary syntax as in ``self.config["mongo_database"]`` or
dot notation as in ``self.config.mongo_database``.


connect directive
-----------------

core4 configuration provides a special directive ``connect`` to manage database
connection settings. This statement parses authentication/hostname information,
database and collection name::

    coll = connect("mongodb://user:pwd@localhost:27017/testdb/result")

If no hostname is specified, then the connection URL is taken from variable
``mongo_url``. If no database name is specified, then it is taken from variable
``mongo_database``. Therefore, the following configuration examples all
cascade to the same connection settings::

    from core4.config import connect

    mongo_url = "mongodb://usr:pwd@localhost:27017"
    mongo_database = "db"

    section1 = {
        "result1": connect("mongodb://usr:pwd@localhost:27017/db/result"),
        "result2": connect("mongodb://db/result"),
        "result3": connect("mongodb://result")
    }

Access to this configuration example proofs that all three collection objects
constructed with the :class:`.connect` statement point to the same MongoDB
collection::

    import core4.base

    example = core4.base.CoreBase()
    c = example.config.section1
    c.result1.info_url == c.result2.info_url == c.result3.info_url


example
-------

The power of core4 configuration principles is best described with an example.
In this scenario a plugin has been created for an account named ``account1``.
As part of the automation workflow for this account some 3rd party web API is
used to download data on a regular basis. The plugin configuration is supposed
to provide API authorisation data, the URL for the web service as well as the
target database and collection to store the downloaded data.

Therefore the plugin developer has created a section ``api`` in the plugin
configuration file ``account1.py`` located in the root package directory.
Furthermore the developer directs all database access to the default database
for this plugin ``db1``::

    # file: account1/account1.py

    from core4.config.directive import connect

    account1 = {
        "api": {
            "username": "prod-user",
            "password": None,
            "url": "https://example.org/api/v1/download"
        },
        "mongo_database": "db1",
        "download_collection": connect("mongodb://download")
    }


Since the plugin configuration is version controlled and part of the code
repository, the developer provides the (default) API user, but no sensitive
data, e.g. the API password.

During development of the plugin, the developer works with the following user
configuration file located at ``~/core4/local.py``::

    # file: ~/core4/local.py

    mongo_url = "mongodb://localhost:27017"

    account1 = {
        "api": {
            "username": "test-user",
            "password": "123456"
        }
    }


This setup allows the developer to use his or her ``test-user`` with valid
credentials during implementation and to address the local MongoDB instance at
``mongodb://localhost:27017/db1/download``.

After implementation is complete and during deployment the operator extends the
core4 system configuration in production located at ``/etc/core4/local.py``
with::

    # file: /etc/core4/local.py (excerpt)

    mongo_url = "mongodb://core:mongosecret@mongodb.prod:27017"

    account1 = {
        "api": {
            "password": "secret"
        }
    }

This production setup provides actual credentials for the (default) API user
``prod-user`` and the production database located on server ``mongodb.prod``.

The fully qualified download collection now points to
``mongodb://core:mongosecret@mongodb.prod:27017/db1/download``

After several weeks with downloaded data the need arises to aggregate the data
into a reporting collection. The developer, who has read-only access grants at
``mongodb.prod`` extends the plugin configuration ``account1.py`` with::

    # file: account1/account1.py

    from core4.config.directive import connect

    account1 = {
        "api": {
            "username": "prod-user",
            "password": None,
            "url": "https://example.org/api/v1/download"
        },
        "mongo_database": "db1",
        "download_collection": connect("mongodb://download"),
        "report_collection": connect("mongodb://report")
    }


To simplify implementation activities the developer extends his
``~/core4/local.py`` to read (only) the downloaded data from production with::

    # file: ~/core4/local.py

    mongo_url = "mongodb://localhost:27017"

    account1 = {
        "api": {
            "username": "test-user",
            "password": "123456"
        },
        "download_collection": connect("mongodb://pete:pwd@mongodb.prod/db1/report")
    }


This example show, how to create valid plugin configuration settings which can
be overwritten easily for development as well as production needs. With the
``connect`` directive the developer furthermore can easily create cross
database connections which simplifies implementation activities if the
developer has for example read-only access to production data.

All configuration files - ``account1.py``, ``~/core4/local.py`` and
``/etc/core4/local.py`` in this example - can be created and maintained
independent of each other.


.. _Python as configuration files: https://softwareengineering.stackexchange.com/questions/351126/how-bad-of-an-idea-is-it-to-use-python-files-as-configuration-files
.. _Matteo's comment: https://softwareengineering.stackexchange.com/a/351167