.. _tools:

##################
command line tools
##################

.. _coco:

``coco`` - core4 control
########################

Use *coco* to interact with the core4 backend and frontend in the most relevant
touchpoints. These includes:

*PROJECT MANAGEMENT*

* create a new project with ``coco --init``

*DAEMON CONTROL*

* start a worker with ``coco --worker``
* start a scheduler with ``coco --scheduler``
* start an application server with ``coco --application``
* stop all daemon with ``coco --halt``

*SETUP CONTROL*

* list running daemons with ``coco --alive``
* show setup information with ``coco --who``
* enumerate available jobs across projects with ``coco --jobs``
* enumerate installed projects with ``coco --project``

*JOB MANAGEMENT*

* enqueue new job with ``coco --enqueue``
* display running and pending job summary with ``coco --info``
* display running and pendinng job information with ``coco --listing``
* show job details with ``coco --detail``
* remove jobs with ``coco --remove``
* kill jobs with ``coco --kill``
* restart jobs with ``coco --restart``

*RELEASE MANAMGENET*

* build webapps with ``coco --dist``
* prepare new release with ``coco --build``
* finalize release with ``coco --release``

*MAINTENANCE*

* pause system operations or job processing for a specific project with
  ``coco -pause``
* resume with ``coco --resume``
* display system state with ``coco --mode``

See more details with ``coco --help``.


.. _chist:

``chist`` - core4 history
#########################

Use ``chist`` command line tool to display logging output:

* set the ``--start``/``--end`` filters with a datetime, date or relative
  period in hours (h), days (d), weeks (w) or months (m)
* filter the logging ``--level`` by defining the lower bound with DEBUG, INFO,
  WARNING, ERROR or CRITICAL
* filter for ``--project``, ``--hostname``, ``--username``
* filter for the ``--qual_name`` matching from the left
* filter for object ``--identifier`` matching from the right
* filter for ``--message`` using regular expression
* ``--follow`` the output appended data as the logging grows. The default
  polling period is 1 second. Set the polling period with an argument, i.e.
  ``chist -f 15`` to follow in 15 seconds periods.

Default matching is case-insensitive. Change this behavior for options text
filters with ``--case-sensitive``.

See more details with ``chist --help``
