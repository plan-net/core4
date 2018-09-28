.. _job:

CoreJob
=======

Introduction
------------

CoreJobs are the entry-point for the Data-Scientist to encapsulate his
code into the core4 fault-tolerent distributed execution framework.

Principles
----------

CoreJobs implement the logic layer of the core architecture. Jobs can
broadly be categorised into

CoreJobs can be broadly catagorised int:

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
