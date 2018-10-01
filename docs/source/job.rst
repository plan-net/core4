.. _job:

CoreJob
=======

Introduction
------------


As of today, modern Data-Scientists use a variety of python- and R-modules both Open- and Closed-Source to create
relevant insights based on multiple sets of data from many different sources.

Core4-Jobs are for those Data-Scientists and -Engieneers to achive fault-tolerant automatization of all
needed steps of creating those insights without having the user think about the underlying software or hardware.

core4 takes care of everything that is essential to using and operating such a distributed system,
from central logging and configuration to deployment, all this while scaling to the 100ths of servers.

todo: first small example....



A job can have multiple states, depending on its configured runtime-behaviour:

.. figure:: _static/job_states.png
   :scale: 100 %
   :alt: job_states

Jobs are guided via config- or class-variables,
A most basic subset of these settings are descriped in the table below:

 ================= ====================================================================
          property description
 ================= ====================================================================
              args arguments passed to the job
            author author of the job
             chain jobs that are to launch after the current job finishes
         defer_max overall Sum of seconds a job can be deferred
        defer_time time inbetween defers
        dependency dependencies that have to be finished before the job can be launched
        error_time seconds to wait before a job is restarted after a failure
             force ignore available ressources, force start a job
      max_parallel max. number of parallel running jobs of current type
             nodes nodes the job can run on
          priority priority with 0 being the lowest
          schedule job schedule in crontab-syntax
             state current state of the job (see the graphic above)
         wall_time seconds before a job with no feedback turns to zombie.
 ================= ====================================================================

For further information please visit: :ref: config.




todo: job-states, uebergaenge, wichtige vars, link zu allen anderen vars, link zu configuration,

Examples
--------

-- code --

Principles
----------

CoreJobs implement the logic layer of the core architecture. Jobs can
broadly be categorised into

CoreJobs can be broadly categorised into:

-   extraction jobs, scanners and feed readers representing inbound
    interfaces

-   load jobs for saving inbound data to the database

-   transformation, analysis and aggregation job

-   export jobs and feeds representing the outbound interfaces

This differentiation is only from a conceptional view point. All jobs
are irrespective of their goal and purpose implemented as CoreJobs.

Best practices
--------------

When writing CoreJobs (or any part of software really), it is advisable
to adhere to the following design paradigms:

-   divide and conquer

-   do one thing and do it well

-   KISS - keep it simple and stupid

Both guidelines are interrelated. The dotadiw (do one thing and do it
well) philosophy is borrowed from the general Unix philosophies.
Actually, the design of automation jobs should follow the first four out
of nine guidelines:

-   Small is beautiful.

-   Make each program do one thing well.

-   Build a prototype as soon as possible.

-   Choose portability over efficiency.


Out of experience we would recommend to adhere to the following
principles also:

-   design your applications with restartability in mind.

-   create Data-Structures that are idempotent on multiple loads of the
    same data.

-   implement continuity-checks if data is continuos.

-   robustness before neatness.

-   work silently, fail noisily.

-   build modular and reusable classes and functions.

-   choose meaningful function-/class-/variable-names




As of today, modern Data-Scientists use a variety of python- and R-modules both Open- and Closed-Source to create
relevant insights based on multiple sets of data from many different sources.

Core4-Jobs are for those Data-Scientists and -Engieneers to achive fault-tolerant automatization of all
needed steps of creating those insights without having the user think about the underlying software or hardware.

core4 takes care of everything that is essential to using and operating such a distributed system,
from central logging and configuration to deployment, all this while scaling to the 100ths of servers.


A first example, which loads the data from an excel into the database is as follows:

-- code --




