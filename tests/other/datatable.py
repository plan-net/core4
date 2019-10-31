"""
hook a shell with

    $ cd
    $ cd PycharmProjects/core4
    $ source enter_env
    $ python tests/other/datatable.py

visit http://0.0.0.0:5001, login and use the "CoreDataTable example" widget

resources:

    * other.datatable ... this example handler and api container
    * other/table/table1.html ... the example HTML page including extra elements
                                  like pagination, parameters etc. not yet
                                  included in the datatable component
    * core4.data.table ... the Python class CoreDataTable used by TableHandler1
    * core4/api/v1/request/_static/jexcel/datatable.js ... the javascript class
"""
import random

import bson.objectid
import datetime

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.data.table import CoreDataTable


def make_data(coll, count=60):
    segment = ["segment A", "segment B", "segment C", "segment D",
               "segment E"]
    coll.delete_many({})
    t0 = datetime.datetime(2014, 1, 1)
    for i in range(count):
        t0 += datetime.timedelta(hours=4)
        coll.insert_one({
            "timestamp": t0,
            "idx": i + 1,
            "real": random.random() * 100.,
            "value": random.randint(1, 20),
            "segment": segment[random.randint(0, 4)]
        })
    return coll


class TableHandler1(CoreRequestHandler):

    author = "mra"
    title = "CoreDataTable example"

    # this is the API handler delivering 1) json data using core4 pagination
    # and 2) a datatable example HTML including all required css, js and
    # initialisation code

    async def get(self, path=None):

        # data pager

        coll = self.config.tests.data1_collection

        async def _length(filter):
            return await coll.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            return await coll.find(filter).sort(sort_by).skip(skip).limit(
                limit).to_list(limit)

        def _hook(obj):
            # special json hook to parse typed mongodb query
            # the hook parses 1) datetime objects and 2) objectid objects
            #
            # example of a date range filter converting a string into a valid
            #   datetime object:
            #
            # { "timestamp": { "$gte": { "$datetime": "2014-04-01T00:00:00" } } }
            #
            # example of a object id filter converting a string into a valid
            #   bson object id:
            #
            # { "_id": { "$objectid": "5d8af9cbad70712cbe0521f7" } }
            for key, value in obj.items():
                if isinstance(key, str):
                    if key == "$datetime":
                        try:
                            obj = datetime.datetime.strptime(
                                value, "%Y-%m-%dT%H:%M:%S.%f")
                        except:
                            obj = datetime.datetime.strptime(
                                value, "%Y-%m-%dT%H:%M:%S")
                    elif key == "$objectid":
                        obj = bson.objectid.ObjectId(value)
            return obj

        # args parsing similar to core4 standard pagination

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        sort_by = self.get_argument("sort", as_type=list,
                                    default=[['segment', 1]])
        filter = self.get_argument("filter", as_type=dict, default={},
                                   dict_decode=_hook)
        table = CoreDataTable(
            self.application.container.get_root("table1/data"),
            # data endpoint is the same with Accept: application/json
            height="320px",
            column=[
                # for format specs see https://docs.python.org/3/library/string.html#format-specification-mini-language
                {"name": "timestamp", "title": "Timestamp",
                 "format": "{:%d.%m.%Y %H:%M:%S}", "visible": True,
                 "align": "center"},
                {"name": "_id", "title": "ID", "format": "{:}", "visible": True,
                 "align": "left"},
                {"name": "idx", "title": "INDEX", "format": "- {:d} -",
                 "visible": True, "align": "center"},
                {"name": "segment", "title": "GRUPPE", "format": "{:s}",
                 "visible": True, "align": "right"},
                {"name": "real", "title": "ZAHL", "format": "{:1.4f} €",
                 "visible": True, "align": "right"},
                {"name": "value", "title": "GANZZAHL", "format": "{:012d}",
                 "visible": True, "align": "left"}
            ],
            per_page=per_page,
            current_page=current_page,
            sort_by=sort_by,
            filter=filter,
            length=_length,
            query=_query
        )

        if path == "/data":
            # render page data
            print(coll)
            self.reply(await table.page())
        else:
            # render example page with CoreDataTable object dt
            self.render(
                "table/table1.html",
                dt=table,
            )


class TableServer1(CoreApiContainer):
    root = "/test"
    rules = [
        # /test/table1 ... HTML
        # /test/table1/data ... json data pages
        (r"/table1(.*)", TableHandler1)
    ]


if __name__ == '__main__':
    # create test data
    import pymongo
    mongo = pymongo.MongoClient("mongodb://core:654321@localhost:27017")
    make_data(mongo.core4test.data1, 1000)

    # change default database
    import os
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
    from core4.api.v1.tool.functool import serve

    # start server including core4 standard API
    serve(TableServer1, routing="0.0.0.0:5001")
