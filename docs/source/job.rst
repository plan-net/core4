CoreJob
=======


Job principles
--------------

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


Example:
--------
.. code-block:: python

    import requests
    import re

    import core.queue.job
    import core.util


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


**Explanation:**
    1. All jobs inherit from core.queue.job.Job.
    2. Using crontab syntax this job starts each five minutes.
    3. If the job fails, then retry another 4 times ...
    4. but wait for two minutes before each trial.
    5. The job’s .execute() method is called when compute resources are available.
    6. The bild.de RSS feed can be configured and defaults to the given url.
    7. This is an INFO message to core central logging system. This is the Python Standard logging logger knowing DEBUG, INFO, WARNING, ERROR and CRITICAL level messages.
    8. Use requests to get the feed.
    9. Remove all XML tags and split words. I know you can do better with exact parsing of the RSS feed.
    10. Build result using CORE’s own timestamp, not thinking about timezones.
    11. Get list of interest terms from core.config and search LIEBE and HASS by default.
    12. Loop all terms of interest
    13. Count the number of term occurrences.
    14. Update result dict.
    15. Be verbose in DEBUG mode (depends on CORE plugin default configuration, here).
    16. Get MongoDB connection to collection term.count. Authorisation and access permission management is taken from CORE plugin configuration and the security profile of the caller (man or machine).
    17. Insert result into the MongoDB. Note that the job adds some extra information for tracking purposes.


