.. _job:

####
jobs
####

job principles
==============

core4 Jobs represent single or multiple Tasks that are to be executed within the Framework.
Jobs give access to the core4 configuration, core4 queue and the database.

.. _philosophy:

With the core automation framework we adhere to the following two design paradigms:

#. **divide and conquer** - objective is always to break down a job into two or more jobs until these become
   simple enough to be solved directly.
#. **do one thing and do it well**

Both guidelines are interrelated. The *dotadiw* (do one thing and do it well) philosophy is borrowed from the general
Unix philosophies. Actually, the design of automation jobs should follow the first four out of nine guidelines.

* **Small is beautiful.**
* **Make each program do one thing well.**
* **Build a prototype as soon as possible.**
* **Choose portability over efficiency.**


Out of experience we would recommend to adhere to the following principles also:

.. _best practices:

#. design your applications with restartability in mind.
#. create Data-Structures that are idempotent on multiple loads of the same data.
#. implement continuity-checks if data is continuos.


example
=======

.. code-block:: python
   :linenos:

   import requests
   import re

   import core4.base.job
   import core4.util


   class FirstJob(core.base.job.Job):

       """
       Each 30 minutes, this job counts the occurrences of terms LIEBE and
       HASS in the news feed of Axel Springer's bild.de.
       """

       author = "mra"
       schedule = "*/30 * * * *"
       attempts = 5
       error_time = 120

       def execute(self, *args, **kwargs):
           url = self.config.test.get('url',
                                      "https://www.bild.de/rssfeeds/vw-alles"
                                      "/vw-alles-26970192,"
                                      "dzbildplus=true,"
                                      "sort=1,"
                                      "teaserbildmobil=false,"
                                      "view=rss2,"
                                      "wtmc=ob.feed.bild.xml")
           self.logger.info('crawling bild.rss = [%s]', url)
           rv = requests.get(url)

           words = re.sub(
               '\s+', ' ', re.sub('\<.*?\>', '', rv.content, flags=re.DOTALL)
           ).split()
           result = {'create': core4.util.now()}
           terms = self.config.test.get("terms", ["liebe", "hass"])
           for term in terms:
               found = sum([1 for w in words if w.lower().find(term)>=0])
               result.setdefault(term, found)
               self.logger.debug('count [%d] of [%s]', found, term)

           target = self.config.get('target', 'term.count')
           target.insert_one(result)


explanation
-----------

* **line 8** - all jobs inherit from :class:`core4.queue.job.Job`.
* **line 16** - using crontab syntax this job starts each five minutes.
* **line 17** - if the job fails, then retry another 4 times
* **line 18** - but wait for two minutes before each trial.
* **line 20** - the job’s ``.execute()`` method is called when compute
  resources are available.
* **line 21** - the RSS feed URL can be configured and defaults to the given
  url
* **line 29** - this is an *INFO* message to core4 central logging system. This
  is the Python Standard logging logger knowing *DEBUG*, *INFO*, *WARNING*,
  *ERROR* and *CRITICAL* level messages.
* **line 30** - use :mod:`requests` to get the feed.
* **line 32** - remove all XML tags and split words. I know you can do better
  with exact parsing of the RSS feed.
* **line 35** - build result using core4's own timestamp, not thinking about
  timezones.
* **line 36** - get list of interest terms from :mod:`core4.config` and search
  ``LIEBE`` and ``HASS`` by default.
* **line 37** - loop all terms of interest,
* **line 38** - and count the number of term occurrences.
* **line 39** - update result dict.
* **line 40** - be verbose in *DEBUG* mode (depends on plugin default
  configuration, here).
* **line 42** - get MongoDB collection term.count. Authorisation and access
  permission management is taken from core4 plugin configuration and the
  security profile of the caller (man or machine).
* **line 43** - insert result into the MongoDB. Note that the job adds some
  extra information for tracking purposes.
