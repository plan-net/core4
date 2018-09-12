.. _logging:

#######
logging
#######

There are three main logging targets used by core4 components:

#. the console ``STDOUT``
#. the console ``STDERR``
#. the mongo collection ``sys.log``

The core4 logger name is ``core4`` and replicates the :meth:`.qual_name()` of
the class, e.g. ``core4.base.main.CoreBase`` for :class:`.CoreBase`. All
plugin based classes have a special logger name starting with ``core4.plugin``.

To turn on logging to ``STDOUT``, ``STDERR`` or MongoDB set the requested
logging level, for example::

    logging = {
        "stderr": "DEBUG",
        "stdout": None,
        "mongodb": "INFO",
    }


For MongoDB logging additionally define the target collection ``sys.log``,
i.e.::

    sys = {
        "log": connect("mongodb://sys.log")
    }


custom logging setup
====================

You can add additional custom logging handlers by setting the core4
configuration setting ``logging.extra``. See for example
`dict based logging setup`_ and Fang's coding notes on
`good logging practices`_. If ``logging.extra is None`` then no custom logging
will be set up.


extra logging attributes
========================

core4 defines the following additional logging attributes:

* ``username``
* ``hostname``
* ``identifier``
* ``qual_name``

These special attributes are supposed to facilitate the filtering of logging
messages while reviewing core4 activities in operations (see :ref:`chist`).

Use ``qual_name`` to filter all log messages which have been created by a
class inherited from :class:`.CoreBase`.

The special attribute ``identifier`` encapsulates all log messages of the
following objects:

#. core4 jobs - the ``identifier`` represents the ``job_id``
#. core4 API resources - the ``identifier`` represents the ``request_id``
#. core4 workers - the ``identifier`` represents the worker's ``hostname``
#. core4 scheduler - the ``identifier`` represents the scheduler`s ``hostname``

.. note:: All objects created in the namespace of a job, API resource, worker
          or scheduler automatically inherit the identifier from these objects.
          This behavior ensures that a log filter captures all activities
          which occured during execution.


logging of exceptions
=====================

core4 provides a special means to handle exceptions. In the event of a logging
message at level ``logging.CRITICAL``, all log messages below the specified log
level defined for MongoDB will be logged belated.

.. note:: Later logging of log messages below the specified level only works
          for logging into MongoDB (``logging.mongodb``). Therefore this
          setting only applies if logging into ``sys.log`` is defined.


logging startup
===============

All classes derived from :class:`.CoreBase` attach to the ``core4`` root logger
with a :class:`logging.NullHandler`. Opening the logging targets described
above is the responsibility of the application (e.g. the worker, the command
line tools :ref:`coco <coco>`, :ref:`chist <chist>`, :ref:`cadmin <cadmin>`,
and web applications (see `logging howto`_).

Class :class:`.CoreLoggerMixin` adds a method :meth:`.setup_logging` to classes
based on :class:`.CoreBase`. This method starts logging as in the following
example.

.. code-block:: python
   :linenos:

   from core4.base import CoreBase
   from core4.logger import CoreLoggerMixin

   class MyApp(CoreBase, CoreLoggerMixin):

       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.setup_logging()


logging guideline
=================

Best practice is to use as few log levels as possible. The rational is to
minimise confusion and to have a simple and clear log level convention. This
convention is to use

* **DEBUG** - for development, pre-production, and diagnostic purposes
* **INFO** - to indicate main events and the start or end of main operations.
  If for example a service or job produces more than 5-7 info messages in total
  and more than 1 info message about main processing steps per minute, the
  developer should consider to use more debug level messages.
* **WARNING** - to indicate unexpected situations and oddities which are still
  handled by the system. A significant increase in such oddities require
  further analysis and therefore core4 operators have to revisit the amount and
  nature of warnings on a regular basis.
* **ERROR** - used to indicate fatal operations. Errors require operator
  attention since the operation did not complete as expected and the intended
  workflow did not complete. The core4 system is fault tolerant and therefore a
  job or service might recover from these errors by being restarted. If for
  example a job fails on a regular basis due to service downtime of an external
  system this error should be translated into a warning. Errors should be
  reserved for unexpected situations.
* **CRITICAL** - to indicate that a job or service has been halt due to an
  unexpected or unhandled situation or due to an exception.

To cut a long story short: *WARNING* and *ERROR* level messages should be
reviewed on a regular bases. *ERROR* level messages require attention.
*CRITICAL* messages require immediate attention.

Since *CRITICAL* messages require immediate attention, the list of these
exception is listed below:


.. _logging howto: https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
.. _dict based logging setup: https://docs.python.org/2/howto/logging-cookbook.html#an-example-dictionary-based-configuration
.. _good logging practices: https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
