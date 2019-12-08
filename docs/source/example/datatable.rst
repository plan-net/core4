##########
data table
##########

core4os ships a request handler
:class:`core4.api.v1.tool.datatable.CoreDataTableRequest` to easily render
tabular data.

This document demonstrates the usage of this handler. Before we start
implementing an API service with an appropriate handler we have to create some
sample data.

data preparation
================

Let's create a MongoDB collection with some data.

.. code-block:: python

    mongo = pymongo.MongoClient("mongodb://core:654321@localhost:27017")
    coll =  mongo.core4test.data1
    segment = ["segment A", "segment B", "segment C", "segment D",
               "segment E"]
    coll.delete_many({})
    t0 = datetime.datetime(2014, 1, 1)
    for i in range(1000):
        t0 += datetime.timedelta(hours=4)
        coll.insert_one({
            "timestamp": t0,
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })

This creates 10000 records in MongoDB database ``core4test``, collection
``data1``.

We will now implement a request handler delivering this data.


column specification
====================

The following list defines the columns. We will use it in the next step.

.. code-block:: python

    COLS = [
        {"name": "_id",       "key": True, "hide": True, "editable": False},
        {"name": "idx",       "label": "#",           "format": "{:05d}"},
        {"name": "segment",   "label": "Segment",     "format": "{:s}" ,
        {"name": "real",      "label": "Realzahl",    "format": "{:+1.3f}" ,
        {"name": "value",     "label": "Ganzzahl",    "format": "{:d}" ,
        {"name": "timestamp", "label": "Zeitstempel", "format": "{:%d.%m.%Y at %H:%M:%S}"}
    ]

With one exception of column ``_id`` all columns have a label and a format.
Column ``_id`` is defined as *hidden* and not *editable* but as the *key*
column. This is because the ``_id`` acts as the mere identifier of the data row.
No need to display it.

We will now assign this column definition to our request handler.


request handler
===============

Inheriting from :class:`core4.api.v1.tool.datatable.CoreDataTableRequest` we
will implement a request handler delivering the data from MongoDB collection
``core4test.data1``.

.. code-block:: python

    class TableHandler(CoreDataTableRequest):

        author = "mra"
        title = "datatable example"

        column = COLS

        async def length(self, filter):
            pass

        async def query(self, skip, limit, filter, sort_by):
            pass


The three elements ``column``, ``.length`` and ``.query`` are the minimum
requirements of a data table request handler.

The ``.length`` method must return the number of records after applying a
``filter`` argument. The ``.query`` method must return the records. This method
is supposed to process the ``filter`` argument, too. Furthermore it must respect
the number of records to *skip*, the number of records to retrieve (*limit*) and
the expected sort order (*sort_by*).

The following snippet implements the final version of the request handler.

.. code-block:: python

    class TableHandler(CoreDataTableRequest):
        author = "mra"
        title = "datatable example"

        column = COLS

        @property
        def collection(self):
            return self.config.tests.data1_collection

        def myfilter(self, filter):
            query = self.convert_filter(filter)
            if not isinstance(query, dict):
                query = {}
            return query

        async def length(self, filter):
            return await self.collection.count_documents(self.myfilter(filter))

        async def query(self, skip, limit, filter, sort_by):
            return await self.collection.find(
                self.myfilter(filter)).sort(
                    sort_by).skip(
                        skip).limit(
                            limit).to_list(
                                None)

The implementation wraps collection access into a property method
``.collection`` and uses ``.myfilter`` method to to preprocess the passed
``filter`` attribute. This attribute is always passed as a plain string and
requires further processing before it can be passed to the query.

Before we turn to the usage of this handler, we conclude this section with the
api container and the usual Python ``__main__`` section to use the web service
with ``python``.

.. code-block:: python

    class TableServer(CoreApiContainer):

        rules = [
            ("/table", TableHandler)
        ]

    if __name__ == '__main__':
        from core4.api.v1.tool.functool import serve
        serve(TableServer)


The full Python code can be found in the core4os repository, directory
``core4/tests/other/datatable.py``.


using the handler
=================

The following example session requires a running API container and uses
``requests`` module to work with the data.

.. code-block:: python

    from  requests import get, post

    url = "http://localhost:5001/tests/table"
    username = "admin"
    password = "hans"

    login = get(
        "http://localhost:5001/core4/api/v1/login?username=%s&password=%s" %(
            username, password))

    # get results with default settings, display available keys
    get(url, cookies=login.cookies).json()["data"].keys()
    # show pagination
    get(url, cookies=login.cookies).json()["data"]["paging"]
    # show columns
    get(url, cookies=login.cookies).json()["data"]["column"]
    # show page 2
    post(url, json={"page": 1}, cookies=login.cookies).json()["data"]["paging"]
    # show page 2 with 25 per page and save settings with POST
    post(url, json={"page": 1, "per_page" :25},
         cookies=login.cookies).json()["data"]["paging"]
    # show page 3 with saved settings (25 records per page)
    post(url, json={"page": 2}, cookies=login.cookies).json()["data"]["paging"]
    # show only 2 columns, change column order and save settings again
    selected_column = [
        {'hide': False, 'name': 'segment'},
        {'hide': False, 'name': 'real'},
        {'hide': True, 'name': '_id'},
        {'hide': True, 'name': 'idx'},
        {'hide': True, 'name': 'value'},
        {'hide': True, 'name': 'timestamp'}]
    post(url, json={"column": selected_column},
         cookies=login.cookies).json()["data"]["paging"]
    # show page 4 with saved settings
    get(url + "?page=3", cookies=login.cookies).json()["data"]["column"]
    post(url, json={"page": 3}, cookies=login.cookies).json()["data"]["column"]
    # download data with saved settings
    for line in get(url + "?download=1", cookies=login.cookies, stream=True):
        print(line.decode("utf-8"), end="")
    # download all columns but do not touch saved settings
    for line in get(url + "?download=1&reset=True", cookies=login.cookies, stream=True):
        print(line.decode("utf-8"), end="")
    # go back to saved settings
    for line in post(url, json={"download": True}, cookies=login.cookies, stream=True):
        print(line.decode("utf-8"), end="")

Before we turn to the frontend side, please have a look at all available options
at :ref:`datatable`.