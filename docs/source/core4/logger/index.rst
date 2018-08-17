logger
======

Package ``core4.logger`` implements all components required for the core4
logging system.

core4 uses the Python standard :mod:`logging` module to deliver the following
features:

* configuration of a console log handler (STDERR and STDOUT)
* configuration of centralised logging into MongoDB collection ``sys.log`` (see
  :class:`.MongoLoggingHandler`)
* custom configuration of package and module logging

There are various extra attributes passed by a custom logging adapter
:class:`.CoreLoggingAdapter` and saved into MongoDB collection ``sys.log`` by a
custom logging handler :class:`.MongoLoggingHandler`. See
:class:`.MongoLoggingHandler` for a list of attributes.

All classes inherited from :class:`.CoreBase` feature this logging. All
application objects need to mixin :class:`.CoreLoggerMixin` and call
:meth:`.CoreLoggerMixin.setup_logging` to start logging as specified in section
``logging`` (see :ref:`logging`).

.. toctree::

   mixin
   handler
   adapter
   filter
   exception


