.. _job:

CoreJob
=======

Introduction
------------


As of today, modern Data-Scientists use a variety of python- and R-modules both Open- and Closed-Source to create
relevant insights based on multiple sets of data from many different sources.

Core4-Jobs are for those Data-Scientists and -Engineers to achieve fault-tolerant automation of all needed steps of
creating those insights without having the user think about the underlying software or hardware.


core4 takes care of everything that is essential to using and operating such a distributed system,
from central logging and configuration to deployment, all this while scaling to the 100ths of servers.

CoreJobs
--------

CoreJobs implement the logic layer of the core architecture and enables the user to fully automate their business logic
within a fault-tolerant distributed system. Core    Jobs are the starting point for any Data-engineer or -scientist and
provides a lot of possibilities to easily control the runtime-behavior within the framework.

Example
--------

.. code-block:: python

    class FirstJob(core.queue.job.Job):                                       # [1]

        """
        Each 30 minutes, this job counts the occurrences of terms LIEBE and
        HASS in the news feed of Axel Springer's bild.de.
        """

        author = "mra"
        schedule = "*/30 * * * *"                                              # [2]
        attempts = 5                                                           # [3]
        error_time = 120                                                       # [4]

        def execute(self, *args, **kwargs):                                    # [5]
            url = self.config.get('bild.rss',
                                  "https://www.bild.de/rssfeeds/vw-alles"
                                  "/vw-alles-26970192,"
                                  "dzbildplus=true,"
                                  "sort=1,"
                                  "teaserbildmobil=false,"
                                  "view=rss2,"
                                  "wtmc=ob.feed.bild.xml")                     # [6]
            self.logger.info('crawling bild.rss = [%s]', url)                  # [7]
            rv = requests.get(url)                                             # [8]

            words = re.sub(
                '\s+', ' ', re.sub('\<.*?\>', '', rv.content, flags=re.DOTALL)
            ).split()                                                          # [9]
            result = {'create': core.util.now()}                               # [10]
            terms = self.config.get_list('terms', [“liebe”, “hass”])           # [11]

            for term in terms:                                                 # [12]
                found = sum([1 for w in words if w.lower().find(term)>=0])     # [13]
                result.setdefault(term, found)                                 # [14]
                self.logger.debug('count [%d] of [%s]', found, term)           # [15]

            target = self.config.collection('term.count')                      # [16]
            target.insert_one(result)                                          # [17]


Explanation:

| [1] All jobs inherit from core.queue.job.Job.
| [2] Using crontab syntax this job starts each five minutes.
| [3] If the job fails, then retry another 4 times ...
| [4] but wait for two minutes before each trial.
| [5] The job’s .execute() method is called when compute resources are available.
| [6] The bild.de RSS feed can be configured and defaults to the given url.
| [7] This is an INFO message to core central logging system. This is the Python Standard logging logger knowing: DEBUG, INFO, WARNING, ERROR and CRITICAL level messages.
| [8] Use requests to get the feed.
| [9] Remove all XML tags and split words. I know you can do better with exact parsing of the RSS feed.
| [10] Build result using CORE’s own timestamp, not thinking about timezones.
| [11] Get list of interest terms from core.config and search LIEBE and HASS by default.
| [12] Loop all terms of interest,
| [13] and count the number of term occurrences.
| [14] Update result dict.
| [15] Be verbose in DEBUG mode (depends on CORE plugin default configuration, here).
| [16] Get MongoDB connection to collection term.count. Authorisation and access permission management is taken from CORE plugin configuration and the security profile of the caller (man or machine).
| [17] Insert result into the MongoDB. Note that the job adds some extra information for tracking purposes.


Down below you can find a more detailed instruction about various aspects of writing CoreJobs:


Principles
----------

CoreJobs implement the logic layer of the core architecture. CoreJobs can broadly be categorised into

-   extraction jobs, scanners and feed readers representing inbound
    interfaces

-   load jobs for saving inbound data to the database

-   transformation, analysis and aggregation job

-   export jobs and feeds representing the outbound interfaces

This differentiation is only from a conceptional view point. All jobs
are irrespective of their goal and purpose implemented as CoreJobs.


runtime behavior
----------------

A job can have multiple states, depending on its configured runtime-behavior:

.. figure:: _static/job_states.png
   :scale: 100 %
   :alt: job_states

Switching between these states is either done via configuration-settings or within the code.
A basic subset of configuration-settings is as follows:

 ================= ====================================================================
          property description
 ================= ====================================================================
              args arguments passed to the job
            author author of the job
             chain jobs that are to launch after the current job finishes
         defer_max overall Sum of seconds a job can be deferred
        defer_time time between defers
        dependency dependencies that have to be finished before the job can be launched
        error_time seconds to wait before a job is restarted after a failure
             force ignore available resources, force start a job
      max_parallel max. number of parallel running jobs of current type
             nodes nodes the job can run on
          priority priority with 0 being the lowest
          schedule job schedule in crontab-syntax
             state current state of the job (see the graphic above)
         wall_time seconds before a job with no feedback turns to zombie.
 ================= ====================================================================

Within the code, a job can defer itself::

    self.defer("This job has been defered due to various reasons.")

Or enqueue other jobs by their qual_name::

    self.queue.enqueue("core.queue.job.DummyJob", sleep=120)

Jobs and their states can be monitored and controlled via the "coco" script.
For further information about possible arguments please visit: :ref:`configuration management <config>`.


collection handling
-------------------
core4 ships a great configuration management that can be used to handle multiple different database-connections.
Whether to achieve different databases for different jobs, or to simply read from production data while writing to
your local database, everythings possible.

The example below takes advantage of core4s configuration-inheritance to achieve exactly that.
All keys have to first be set within the plugin-configuration itself so that they can be overwritten by the
user-specific configuration file located in ``~/core4/local.yaml``::

    mongo_url: mongodb://usr:pwd@localhost:27017
    mongo_database: bakery
    cash_register: mongodb://usr:pwd@production_database:27017/registers/cash_register
    low_values: mongodb://low
    mid_values: mongodb://mid
    high_values: mongodb://high



.. code-block:: python

    import core4.util
    from core4.queue.job import CoreJob


    class CalcSum(CoreJob):
        """
        This is just a small example Job that processes bills in the form of:

        {
          "_id": mongodb_object_id
          "date": 2018-01-01,
          "value": 10.0,
          "positions": {
            "pretzel": 2,
            "bun": 1,
            "cake": 3
          }
        }

        and sorts all transactions by their value into the corresponding collection (low, mid, high).
        """
        author = 'mkr'

        def execute(self, *args, **kwargs):
            low = self.config.low_values
            mid = self.config.mid_values
            high = self.config.high_values

            # find todays bills within the input_collection
            today = core4.util.now()
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            data = self.config.cash_register.find({"date": {"$gte": today}})

            # and delete their _id
            for d in data:
                del d['_id']

            # finds all documents with certain values:
            low_data = [i for i in data if i["value"] < 5]
            mid_data = [i for i in data if (i["value"] > 5 and i["value"] < 10)]
            high_data = [i for i["value"] in data if i["value"] > 10]

            # insert found documents into their collection
            low_coll.bulk_write(low_data, ordered=False)
            mid_coll.bulk_write(mid_data, ordered=False)
            high_coll.bulk_write(high_data, ordered=False)



logging
-------

core4 ships with 4 log-levels: CRITICAL/ERROR/WARNING/INFO and DEBUG.
For a job to be able to start logging, it hast to inherit from the ConfigurationMixin:


.. code-block:: python

    from core4.queue.job import CoreJob
    from core4.logger import CoreLoggerMixin


    class Log(CoreLoggerMixin, CoreJob):
        def __init__(self):
            self.setup_logging()


Logging is as simple as calling the required method within self.logger::

    self.logger.critical("A critical, unexpected error appeared")
    self.logger.error("An exception or other expected error has been raised")
    self.logger.warning("This is a warning")
    self.logger.info("This is just another info message")
    self.logger.debug("This is a debug message, it is only shown in case of an error")



You can either use the .format-method of a string or format it the oldschool way::

    self.logger.warning("This value is a double: [%d] and here is its string-representation: [%s]",double(1), str(1))


The DEBUG level will not be logged by default. It will only be written when an error has occured. This way, one can
write multiple DEBUG messages that may help him indentify an error but would otherwise clutter the output.


cookie handling
---------------

For passing arguments from one job to another, or to keep track of job-specific information that hast to be preserved
inbetween multiple runs, CoreCookies can be used.
cookies are identified by the qual_name of the job using them.

Think of it as enhanced browser-cookies, a store for multiple key-value pairs.

Cookies are included within the CoreJob itself, as core automatically keeps track of the last time a worker has tried
to execute the job. A datetime object is stored within the ``last_runtime`` key::

    {
        "_id" : "core.account.core3.queue.job.DummyJob",
        "last_runtime" : ISODate("2018-11-05T09:26:31.156Z")
    }


There are multiple predefined methods for accessing and altering key:value pairs.

For setting fields within the key::

    self.cookie.set(a, 1)
    self.cookie.set(a=1)

For increasing/decreasing a value::

    self.cookie.inc(key, value=1)
    self.cookie.dec(key, value=1)

Compare the given key with the already present value and take the maximum/minimum::

    self.cookie.max(key, value=10)
    self.cookie.min(key, value=5)

Get the value of a key::

    self.cookie.get(key)

Check wheter a key is present::

    self.cookie.has_key(key)

Delete a key:value pair::

    self.cookie.delete(key)

Cookies are often used to keep track of already loaded data e.g. by timestamp::

    self.cookie.set("last_completed": core4.util.now())


structuring of jobs
-------------------
CoreJobs can inherit from any other Classes.
If the inherit from other CoreJobs, all class-properties get inherited too.
Baseclasses themselfs have no schedule and should not be called directly, therefore they can set the ``hidden`` flag,
so that this job will not be listed within a ``coco -j`` and is not visible to the user.

.. code-block:: python

    from core4.queue.job import CoreJob
    from core4.logger import CoreLoggerMixin


    class Parent(CoreJob):
        author = "mkr"
        hidden = True

        def static_mult(x, y):
            return x*y
        ...


    class Child(CoreLoggerMixin, Parent):
        author = "mkr"
        schedule = "* 3 * * *"

        def execute(self, x, y):
            result = self.static_mult(x, y)
            self.logger.info("Got result within the multiplication: [%d]", result)


Best practices
--------------

When writing CoreJobs (or any part of software really), it is advisable
to adhere to the following design paradigms:

-   **divide and conquer**

        divide a big task into multiple smaller parts. The smaller the Task, the easier to scope, to maintain and to
        follow along for others. It also encourages you to follow the next point made here:

-   **do one thing and do it well**

        Do not try to: "I'll fix everything in one method". Separate logical building-blocks from your code, every
        block should only do one single task. This makes it easier to implement changes in the future and helps your
        code to be more readable.

-   **KISS - keep it simple and stupid**
        Robustness and maintainability are more precious than saving a few seconds of time. This however is not valid
        for the correctness of an algorithm. Aim your complexity as high as it has to be but as low as it needs to be.

Both guidelines are interrelated. The dotadiw (do one thing and do it
well) philosophy is borrowed from the general Unix philosophies.
Actually, the design of automation jobs should follow the first four out
of nine guidelines:

-   **Small is beautiful**
        The less code, the easier it is for someone else to understand it, even if that someone is your future self.

-   **Make each program do one thing well**
        do not mix several steps of a processing chain into one document.
        Separate in e.g. load-Job, transform-Job and report-Job.

-   **Build a prototype as soon as possible**
        if you do start programming, try reaching the state of a working prototype as soon as possible. This way,
        you'll notice errors in your concept way earlier, stumble open flaws in your design and you will speed up your
        overall developing speed.

-   **Choose portability over efficiency**
        The more independent your code is from environmental-specific changes, the more robust it will be.
        If you set e.g. set low timeouts, the job may unnecessarily fail when running on high-load nodes.


Out of experience we would recommend to adhere to the following
principles also:

-   **design your applications with restartability in mind**
        There are multiple reasons why a job might fail, including only temporary failures (imagine a website you crawl
        being in maintenance). You can safe yourself a lot of hassle if the job itself knows about its state and can
        simply be restarted without being worried about data-loss or crashing dependencies.

-   **create Data-Structures that are idempotent on multiple loads of the same data**
        you may find yourself in the position where you do not know whether a certain job has processed a particular set
        of data or not. It is elegant to just be able to enqueue that particular job that either only updates the data
        if changes are detected or simply updates already present documents. That way you do not have to worry about
        overwriting critical output.

-   **implement continuity-checks if data is continuous**
        even if your jobs always run to perfection, some of your clients may not. If you have a continuous data stream
        (e.g. a daily reporting via excel) always check that data for completeness. It is easier to let a job fail if
        expected data is not present than to try to retrospectively fix a processing-chain.

-   **robustness before neatness**
        python offers some really nice features for writing clean and easy-to-understand code. An experienced programmer
        might feel tempted to implement the fastest, most efficient way for doing some kind of task. However, speed
        alone should not always be the sole goal of software-design. Keep in mind that many more people might be reliant
        on working on and understanding your code, this even includes your future self.

-   **work silently, fail noisily**
        if your job runs without error, there is no need to log. If however an error occurs, expect to need as much
        information as possible to fix it. Core4 enables you to do this by only logging DEBUG-messages in case of an
        error, but still, you are the one that has to implement these messages.

-   **build modular and reusable classes and functions**
        there always will be multiple parts of a program that can be reused somewhere else. Rather than duplicating
        that code on every place it is needed, simply uncouple the part that is often reused. Not only will your code
        look more clean, you also do save yourself a lot of time if you need to enhance or fix that particular part of
        code.

-   **choose meaningful function-/class-/variable-names**
        choosing simple, yet descriptive names will greatly help you maintain or extend your code.




