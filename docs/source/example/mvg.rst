######################
Departure Times of MVG
######################

The following example has been presented on the Munich Meetup in May 2019. It is
based on the following business question: "What is the next available public
transportation?"

It is based on the following components:

#. A :class:`.CoreJob` to retrieve and save next departure times
#. A :class:`.CoreRequestHandler` to deliver the results


prerequisites
=============

Install core4 (see :doc:`../install/index`), create a project with
``coco --init meetup`` and enter the project environment with
``source meetup/enter_env``.


the core job
============

The following code is sort of the most minimal version of a job. Given the
class resides in a file ``meetup/job.py`` and the job's ``qual_name`` is
``meetup.job.MyJob`` you enqueue the job with
``coco --enqueue meetup.job.Myjob``. Start a worker with ``coco --worker`` to
run the job. Use ``chist`` to see the job's "hello world" greeting. Use
``coco --detail meetup.job.Myjob`` to see the job's "good-bye" output.

.. code-block:: python

    from core4.queue.job import CoreJob


    class MyJob(CoreJob):
        author = "mra"

        def execute(self):
            self.logger.info("hello world")
            print("good-bye")


execute helper method
---------------------

During job implementation, you will want to debug the job and not use the
enqueue/dequeue cycle described above. Use method
:meth:`execute <core4.queue.helper.functool.execute>` as in the following
example:

.. code-block:: python

    from core4.queue.job import CoreJob


    class MyJob(CoreJob):
        author = "mra"

        def execute(self):
            self.logger.info("hello world")
            print("good-bye")


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute
        execute(MyJob)


querying the MVG API
--------------------

Querying the MVG API is easy. See for example `python_mvg_api`_. The following
interactive Python session retrieves current departures from Munich
"Königsplatz":

.. code-block:: python

    import datetime
    import pandas as pd
    import requests

    DEP_URL = "https://www.mvg.de/fahrinfo/api/departure/{id}?footway=0"
    MVG_KEY = "5af1beca494712ed38d313714d4caff6"

    station_id = 110

    url = DEP_URL.format(id=station_id)
    resp = requests.get(url, headers={'X-MVG-Authorization-Key': MVG_KEY})

    if resp.status_code != 200:
        raise RuntimeError("MVG API returned [%s]", resp.status_code)

    print(resp.json())

    data = set()
    for r in resp.json()["departures"]:
        data.add((
            station_id,
            r["product"],
            r["label"],
            r["lineBackgroundColor"],
            r["destination"],
            datetime.datetime.fromtimestamp(
                r["departureTime"] / 1000).replace(second=0)
        ))

    df = pd.DataFrame(data)
    print(df.to_string())


implement the query method
--------------------------

Translate the interactive session above into a job method ``.get_data``.
Migrate the station_id into a method argument and the API key into a
configuration setting. See the example configuration file ``meetup.yaml`` below.

.. code-block:: python

    import datetime
    import requests

    from core4.queue.job import CoreJob

    DEP_URL = "https://www.mvg.de/fahrinfo/api/departure/{id}?footway=0"


    class MyJob(CoreJob):
        author = "mra"

        def execute(self):
            self.logger.info("hello world")
            print("good-bye")

        def get_data(self, station_id):
            url = DEP_URL.format(id=station_id)
            resp = requests.get(url, headers={
                'X-MVG-Authorization-Key': self.config.meetup.mvg.key})

            self.logger.debug("response:\n%s", resp.content)
            if resp.status_code != 200:
                raise RuntimeError("MVG API returned [%s]", resp.status_code)

            data = set()
            for r in resp.json()["departures"]:
                data.add((
                    station_id,
                    r["product"],
                    r["label"],
                    r["lineBackgroundColor"],
                    r["destination"],
                    datetime.datetime.fromtimestamp(
                        r["departureTime"] / 1000).replace(second=0)
                ))

            return data


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute

        execute(MyJob)


implement the execute method
----------------------------

Now implement the ``.execute`` method retrieving the stations in scope from
``meetup.yaml`` and calling ``.get_data``.

.. code-block:: python

    def execute(self):
        for station in self.config.meetup.mvg.station:
            (station_id, distance, *name) = station.split()
            name = " ".join(name)
            self.logger.info("get data of [%s: %s]", station_id, name)
            self.get_data(station_id)


implement materialisation
-------------------------

Final implementation is about saving and updating the data for our own API. We
evaluate the data volume very small and therefore use the job's cookie rather
than a dedicated database collection. Some additional Python logic removes
outdated and hence obsolete data. Using Python tuples we ensure deduplication.

.. code-block:: python

    def execute(self):
        data = {tuple(i) for i in self.cookie.get("departures", set())}
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        data = {d for d in data if d[5] >= now}

        for station in self.config.meetup.mvg.station:
            (station_id, distance, *name) = station.split()
            name = " ".join(name)
            self.logger.info("get data of [%s: %s]", station_id, name)
            update = self.get_data(station_id, distance, name)
            data = data.union(update)

        self.cookie.set("departures", list(data))


job parameters
--------------

The following example parameters ensures the data is sufficiently up-to-date
and cares for MVG downtimes:

.. code-block:: python

    class MyJob(CoreJob):
        author = "mra"
        schedule = "*/15 * * * *"
        attempts = 5
        error_time = 60


the core API handler and container
==================================

The most simple form of a core4 API handler is provided in the following code
snippet. In contrast to a job a handler cannot live by itself. All handlers
require a container to associate it with an endpoint respectively with an URL.


.. code-block:: python

    from core4.api.v1.request.main import CoreRequestHandler
    from core4.api.v1.application import CoreApiContainer


    class MyHandler(CoreRequestHandler):

        """Demo request handler serving MVG data, soon."""

        author = "mra"
        title = "MVG demo handler"

        def get(self):
            self.reply("OK")


    class MyContainer(CoreApiContainer):

        rules = [
            ("/mvg", MyHandler)
        ]


Given the container resides in a file ``meetup/api.py`` and the ``qual_name`` is
``meetup.api.MyContainer`` you start the service with
``coco --app``. Login at http://localhost:5001/core4/api/v1/login and visit
http://localhost:5001/meetup/mvg.


serve helper method
-------------------

During handler implementation, you will want to debug and not use ``coco``
as described above. Use method
:meth:`serve <core4.api.v1.tool.functool.serve>` as in the following example:


.. code-block:: python

    from core4.api.v1.request.main import CoreRequestHandler
    from core4.api.v1.application import CoreApiContainer


    class MyHandler(CoreRequestHandler):

        """Demo request handler serving MVG data, soon."""

        author = "mra"
        title = "MVG demo handler"

        def get(self):
            self.reply("OK")


    class MyContainer(CoreApiContainer):

        rules = [
            ("/mvg", MyHandler)
        ]


    if __name__ == '__main__':
        from core4.api.v1.tool.functool import serve
        serve(MyContainer)



querying the core4 API
----------------------

Before implementing the handler's ``GET`` method we will use an interactive
session to review the data and define an aggregation method using pandas
``groupby`` method to get the very next departure time of each line:

.. code-block:: python

    from meetup.job import MyJob
    import pandas as pd
    import numpy as np
    import datetime

    data = MyJob().cookie.get("departures")
    len(data)

    df = pd.DataFrame(
        data, columns=[
            "station",
            "product",
            "label",
            "color",
            "destination",
            "departure",
            "distance",
            "name"
        ]
    )
    df.head()

    df["walk"] = df.apply(
        lambda r: (
            r["departure"]
            - datetime.timedelta(
                minutes=np.ceil(r["distance"] / 1000. / 3.5 * 60.))
        ),
        axis=1
    )
    df.head()

    df.sort_values("walk", inplace=True)
    g = df.groupby([
        "station", "product", "label", "destination"]).first()
    df = pd.DataFrame(g)
    df.reset_index(inplace=True)
    df.sort_values("walk", inplace=True)
    df.head()


implement the GET method
------------------------

Now implement the handler's ``.get`` method to summarise the data.

.. code-block:: python

    from core4.api.v1.request.main import CoreRequestHandler
    from core4.api.v1.application import CoreApiContainer

    from meetup.job import MyJob
    import pandas as pd
    import numpy as np
    import datetime


    class MyHandler(CoreRequestHandler):

        """Demo request handler serving MVG data, soon."""

        author = "mra"
        title = "MVG demo handler"

        def get(self):
            data = MyJob().cookie.get("departures")
            df = pd.DataFrame(
                data, columns=[
                    "station",
                    "product",
                    "label",
                    "color",
                    "destination",
                    "departure",
                    "distance",
                    "name"
                ]
            )
            df["walk"] = df.apply(
                lambda r: (
                        r["departure"]
                        - datetime.timedelta(
                    minutes=np.ceil(r["distance"] / 1000. / 3.5 * 60.))
                ),
                axis=1
            )
            df.sort_values("walk", inplace=True)
            now = datetime.datetime.now().replace(second=0, microsecond=0)
            df = df[df.walk >= now]
            g = df.groupby([
                "station", "product", "label", "destination"]).last()
            df = pd.DataFrame(g)
            df.reset_index(inplace=True)
            df.sort_values("walk", inplace=True)
            self.reply(df)


    class MyContainer(CoreApiContainer):

        rules = [
            ("/mvg", MyHandler)
        ]


    if __name__ == '__main__':
        from core4.api.v1.tool.functool import serve
        serve(MyContainer)


The above implementation of the ``GET`` method creates a simple HTML table. This
is done by the ``.reply`` method on the fly. The method renders the output
depending on the requested content type of the HTTP client (e.g. the browser)
and the type of the argument. All Python data types are translated into JSON.
pandas data frames for example are rendered as HTML tables if the client accepts
``text/html``, as CSV if the client accepts ``text/csv`` and as json if the
client accepts ``application/json``. The following code snippet retrieves the
data as a list of dict:

.. code-block:: python

    from requests import get as GET
    import pandas as pd

    resp = GET("http://localhost:5001/meetup/mvg", auth=("admin", "hans"))
    df = pd.DataFrame(resp.json()["data"])
    df.head()


.. note:: You can drive content negotiation with URL parameters as in
          http://localhost::5001/meetup/mvg?content_type=json or
          http://localhost::5001/meetup/mvg?content_type=csv and even.
          http://localhost::5001/meetup/mvg?content_type=text.


the HTML template
-----------------

Using `Jinja2`_ you can further extend the HTML output by implementing a
template. The following file ``mvg.html`` resides in ``meetup/template``.

.. code-block:: HTML

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
        <style>
            body {
                background: #dddddd;
                font-family: Arial;
            }
            table {
                border-collapse: separate;
                border-spacing: 0.2em;
            }
            th,td {
                padding: 0.2em 0.5em;
                border-radius: 0.1em;
            }
            thead th {
                background-color: #ffebe6;
                color: #c32e04;
            }
            td {
              box-shadow: inset 1px 3px 5px -3px rgba(0,0,0,0.5);
            }
            td:empty {
                box-shadow: none;
            }
        </style>
    </head>
    <body>

    <h1>MVG Abfahrtszeiten</h1>

    <table>
    {% for record in data %}
    <tr>
        <td bgcolor="{{ record['color'] }}" align="center">{{ record["label"] }}</td>
        <td>{{ record["walk"].strftime("%H:%M") }}</td>
        <td>&rArr;{{ record["name"] }}</td>
        <td>&rArr;{{ record["departure"].strftime("%H:%M") }}</td>
        <td>
            {% if record["product"] != "UBAHN" %}
                {{ record["product"] }}
            {% end if %}
            {{ record["label"] }}{{ record["destination"] }}
        </td>
    </tr>
    {% end for %}
    </table>

    </body>
    </html>


Serve this file by testing the content type requested by the client with
method ``.wants_html`` at the end of the ``.get`` method and return the
rendered HTML if wanted.

.. code-block:: python

    def get(self):
        data = MyJob().cookie.get("departures")
        df = pd.DataFrame(
            data, columns=[
                "station",
                "product",
                "label",
                "color",
                "destination",
                "departure",
                "distance",
                "name"
            ]
        )
        df["walk"] = df.apply(
            lambda r: (
                    r["departure"]
                    - datetime.timedelta(
                minutes=np.ceil(r["distance"] / 1000. / 3.5 * 60.))
            ),
            axis=1
        )
        df.sort_values("walk", inplace=True)
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        df = df[df.walk >= now]
        g = df.groupby([
            "station", "product", "label", "destination"]).first()
        df = pd.DataFrame(g)
        df.reset_index(inplace=True)
        df.sort_values("walk", inplace=True)
        if self.wants_html():
            self.render("template/mvg.html", data=df.to_dict("rec"))
        else:
            self.reply(df)


configuration
=============

If job and API live in a project ``meetup`` then this project requires the
following configuration file ``meetup.yaml``.

.. code-block:: yaml

    DEFAULT:
      mongo_database: meetup

    mvg:
      key: 5af1beca494712ed38d313714d4caff6
      station:
        - 110 209 Königsplatz
        - 170 255 Stiglmaierplatz
        - 15 255 Karlstraße


.. _python_mvg_api: https://github.com/leftshift/python_mvg_api
.. _Jinja2: http://jinja.pocoo.org/docs/2.10/
