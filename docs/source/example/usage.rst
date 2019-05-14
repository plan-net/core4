####################
core usage reporting
####################

With this use case you follow

* the development of a :class:`.CoreJob` and

  * the use of :class:`.Cookie`
  * the principles of cross database access
  * the parsing of arguments and parameter with :class:`.CoreJob`

* the development of :class:`.CoreRequestHandler` and

  * the use of async with :mod:`Motor`
  * the combined use of :mod:`Pandas` to wrangle data and :mod:`.Bokeh` to
    visualize the results

With the forces of a regular job, an API endpoint and a widget this use case
visualises the usage of your core system. As a simple performance metric the
unique number of users who login has been chosen. This KPI can be aggregated by
day, week, month, quarter and year.

But first things first. Let's start with project setup.


project setup
=============

Objective is to create a project hosting all housekeeping activities. The core4
usage report is in scope of this project.

Enter the core4 package::

    cd core4
    source enter_env

Create a new project on the same level::

    cd ..
    coco --init home "Home and Housekeeping" --origin core4/

After successful project creation, leave core4 and enter your newly created
home environment with::

    deactivate
    cd home
    source enter_env


job implementation
==================

The following Python code is the complete module with job
``AggregateCore4Usage``. The purpose of this job is to extract login
information from core4 logging collection ``sys.log`` save condensed
information into the target reporting collection ``login`` in MongoDB database
``home``.

The job class is located in module ``home.usage`` with name
``AggregateCore4Usage`` derived from ``core4.queue.job.CoreJob``.


.. code-block:: python
   :linenos:

   import re
   from datetime import timedelta, datetime

   from core4.queue.job import CoreJob
   from core4.util.node import now
   from dateutil.parser import parse

   parse_date = lambda s: None if s is None else parse(s)


   class AggregateCore4Usage(CoreJob):
       """
       Reads ``sys.log`` as defined by project configuration key
       ``home.usage.sys_log`` and aggregates all user login logging messages into
       collection ``home.login``. Uses job cookie ``offset`` for
       checkpoint/restart.

       This job should is scheduled daily.
       """
       author = "mra"
       schedule = "30 1 * * *"

       def initialise_object(self):
           self.source_collection = self.config.home.usage.sys_log
           self.target_collection = self.config.home.usage.login

       def get_start(self, start, reset):
           if start is None:
               offset = self.cookie.get("offset")
               if reset or offset is None:
                   return self.config.home.usage.start
               return offset
           return parse_date(start)

       def execute(self, start=None, end=None, reset=False, **kwargs):
           start = self.get_start(start, reset)
           end = parse_date(end) or now()
           start = start.date()
           end = end.date()
           if end < start or end > now().date():
               raise RuntimeError("unexpected date range [{} - {}]".format(
                   start, end
               ))
           ndays = (end - start).days + 1.
           self.logger.info("scope [%s] (%s) - [%s] (%s) = [%d] days",
                            start, type(start), end, type(end), ndays)
           n = 0
           while start <= end:
               n += 1.
               self.progress(n / ndays, "work [%s] day [%d]", start, n)
               self.extract(start)
               self.cookie.set(offset=datetime.combine(end, datetime.min.time()))
               start += timedelta(days=1)

       def extract(self, start):
           end = start + timedelta(days=1)
           start = datetime.combine(start, datetime.min.time())
           end = datetime.combine(end, datetime.min.time())
           cur = self.source_collection.find(
               {
                   "created": {
                       "$gte": start,
                       "$lt": end
                   },
                   "message": re.compile("successful login"),
                   "user": {
                       "$ne": "admin"
                   }
               },
               sort=[("_id", -1)],
               projection=["created", "user"]
           )
           data = list(cur)
           self.logger.debug("extracted [%d] records in [%s] - [%s]", len(data),
                             start, end)
           if data:
               self.set_source(str(start.date()))
               self.target_collection.update_one(
                   filter={"_id": start},
                   update={
                       "$set": {
                           "data": [(d["user"], d["created"]) for d in data]
                       }
                   },
                   upsert=True)


   if __name__ == '__main__':
       from core4.queue.helper.functool import execute
       execute(AggregateCore4Usage, reset=True)


This job initialises the source and target collection from core4 configuration
in method ``.initialise`` (line 23). This method is automatically spawned after
job instantiation. The main method ``.execute`` (line 35) initialises the
parameters ``start``, ``end``, ``aggregate`` and ``reset``.

The ``start`` parameter is set with method ``.get_start``. If no explicit start
parameter is provided at job enqueuing, then the start date is taken from the
job's cookie key ``offset`` (line 29). With this mechanic, the job can be
scheduled and starts extracting the data from ``sys.log`` into ``home.login``
with the upper bound of the previous job execution. If the cookie has not been
set, yet, then the very first date to process is taken from home configuration
key ``home.usage.start``.

.. note:: Since JSON has only limited support for date and datetime objects,
          we prefer to parse date/time information as ``str`` objects. We use
          :mod:`dateutil`` module to translate these strings into valid
          datetime objects (see lambda function at line 8).


The main processing loop of the ``.execute`` method starts at line 48. Each
single date of the passed date range (``start`` - ``end``) is processed with
method `.extract`. After successful processing of the date, the job cookie
key ``offset`` is updated. This allows for progressive checkpoint/restart of
job execution.

The ``.extract`` method uses MongoDB's method ``.find`` to retrieve the data
from ``sys.log`` and to save the filtered and condensed data into
``home.login``. The method uses ``.config.home.sys_log`` to address the source
collection (line 59) and ``config.home.login`` to address the target collection
(line 78). Please note the ``.set_source`` command in line 77. Without a
defined source the job cannot insert or update data in the target collection.

Lines 88 - 90 exist for development purposes. The ``execute`` command triggers
job execution without the need to start a dedicated core4 worker process.


API implementation
==================

The API module and corresponding tornado service container are located at
``home.api.v1.usage`` and ``home.api.v1.server`` with and accompanying HTML
template at directory ``home/api/v1/templates``.

The complete code of the API request handler can be found below. For brevity
all code documentation ahs comments have been removed.


.. code-block:: python
   :linenos:

   from datetime import datetime, timedelta

   import pandas as pd
   from bokeh.embed import json_item
   from bokeh.plotting import figure
   from bokeh.resources import CDN
   from core4.api.v1.request.main import CoreRequestHandler
   from core4.util.node import now


   class LoginCountHandler(CoreRequestHandler):
       author = "mra"
       title = "core4 login count"

       async def get(self, mode=None):
           return await self.post(mode)

       async def post(self, mode=None):
           end = self.get_argument("end", as_type=datetime, default=now())
           start = self.get_argument("start", as_type=datetime,
                                     default=end - timedelta(days=90))
           aggregate = self.get_argument("aggregate", as_type=str,
                                         default="w")
           if mode in ("plot", "raw"):
               df = await self._query(start, end, aggregate)
               if mode == "raw":
                   return self.reply(df)
               x = df.timestamp
               y = df.user
               p = figure(title="unique users", x_axis_label='week',
                          sizing_mode="stretch_both", y_axis_label='logins',
                          x_axis_type="datetime")
               p.line(x, y, line_width=4)
               p.title.text = "core usage by users"
               p.title.align = "left"
               p.title.text_font_size = "25px"
               return self.reply(json_item(p, "myplot"))
           return self.render("templates/usage.html",
                              rsc=CDN.render(),
                              start=start,
                              end=end,
                              aggregate=aggregate)

       async def _query(self, start, end, aggregate):
           coll = self.config.home.usage.login.connect_async()
           cur = coll.aggregate([
               {
                   "$match": {
                       "_id": {
                           "$gte": start,
                           "$lt": end
                       }
                   }
               },
               {
                   "$unwind": "$data"
               },
               {
                   "$project": {
                       "_id": 0,
                       "user": {"$arrayElemAt": ['$data', 0]},
                       "timestamp": {"$arrayElemAt": ['$data', 1]}
                   }
               }
           ])
           data = []
           async for doc in cur:
               data.append(doc)
           df = pd.DataFrame(data).set_index("timestamp")
           g = df.groupby(pd.Grouper(freq=aggregate)).user.nunique()
           return g.sort_index().reset_index()


This request handler delivers the same functionality irrespective of ``GET``
or ``POST`` method. Both method handlers process arguments ``start``, ``end``,
and ``aggregate`` (lines 19-23). Furthermore the URL path contains an optional
mode operator1 ``plot`` and ``raw``, e.g.
``http://devops:5001/usage/login/raw``. Without any mode, the handler renders
the widget template ``usage.html`` (line 38) and passes Bokeh prerequisites as
well as the parsed parameters for further processing.

With mode ``plot`` the handler method retrieves the data using method async
``._query`, translates the returned pandas dataframe into plain ``x`` and ``y``
parameters (line 28 and 29), and creates a Bokeh figure (lines 30ff.).

With mode ``raw`` the handler method retrieves the data, too and returns the
data to the front-end.

.. note:: The :meth:`.reply` method provides special processing of the HTTP
          Content-Type header and supports rendering of pandas dataframes as
          HTML, CSV, JSON and text. Use argument ``content_type`` to define
          the requested content type.


Widget template
===============

The following HTML snippet is the widget template used by the API (line 38).

.. code-block:: html
   :linenos:

   <!DOCTYPE html>
   <html lang="en">
   <head>
     {% raw rsc %}
   </head>
   <body>
     <div id="myplot"></div>
     <script>
     fetch('{{ request.path }}/plot?start={{ start }}&end={{ end }}&aggregate={{ aggregate }}')
       .then(
           function(response) {
               return response.json().then(
                   function(res) {
                       return res["data"];
                   }
               )
           }).then(
               function(item) {
                   Bokeh.embed.embed_item(item);
               }
           )
     </script>
   </body>


The ``raw`` directive includes the Bokeh resources rendered (line 39 of the
API request handler, above). The ``div`` *myplot* locates the Bokeh chart. The
``fetch`` statement chain addresses the JSON response delivered by the request
handler (see line 37 of the API request handler, above).


Final commit
============

After successful testing of the job and API commit your changes. Your commits
reside in the default git repository located at ``home/.repos`` which has been
created with your project.

To transfer the repository from your local machine to a remote repository, e.g.
www.github.com, you have to create a new target repository and set the remote
origin with::

   git remote set-url origin https://github.com/<account>/<repository>.git
