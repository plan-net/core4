logging
=======


Overview
--------

core4 uses the Python standard :mod:`logging` module to deliver the following
features:

* simple configuration of a console log handler (STDERR and STDOUT)
* simple configuration of centralised logging into MongoDB collection
  ``sys.log`` (see :class:`.MongoLoggingHandler`)
* simple custom configuration of all package and module logging

There are various extra attributes passed by a custom logging adapter
:class:`.MongoAdapter` and saved into MongoDB collection ``sys.log`` by a custom
logging handler :class:`.MongoLoggingHandler`.

All classes inherited from :class:`.CoreBase` feature this logging. All
application objects need to mixin :class:`.CoreLoggerMixin` and call
:meth:`.CoreLoggerMixin.setup_logging` to start logging as specified in section
``logging``.


MongoLoggingHandler
-------------------

.. autoclass:: core4.logger.MongoLoggingHandler
    :members:


MongoAdapter
------------

.. autoclass:: core4.logger.MongoAdapter
    :members:


CoreLoggerMixin
---------------

.. autoclass:: core4.logger.CoreLoggerMixin
    :members:


