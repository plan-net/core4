import random

import datetime

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.tool.datatable import CoreDataTable, convert

COLS = [
    {
        "name": "_id",
        "label": None,
        "key": True,
        "hide": True,
        "sortable": False,
        "click": None,
        "align": None,
        "format": "{}",
        "editable": False
    },
    {
        "name": "idx",
        "label": "#",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": True,
        "align": "left",
        "format": "{:05d}",
        "editable": True
    },
    {
        "name": "segment",
        "label": "Segment",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "left",
        "format": "{:s}",
        "editable": True
    },
    {
        "name": "real",
        "label": "Realzahl",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "left",
        "format": "{:+1.3f}",
        "editable": True
    },
    {
        "name": "value",
        "label": "Ganzzahl",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "right",
        "format": "{:d}",
        "editable": True
    },
    {
        "name": "timestamp",
        "label": "Zeitstempel",
        "key": False,
        "hide": False,
        "sortable": True,
        "clickable": False,
        "align": "center",
        "format": "{:%Y-%m-%d ... %H:%M:%S}",
        "editable": True
    }
]


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


class TableHandler(CoreRequestHandler):
    author = "mra"
    title = "CoreDataTable example"

    async def _length(self, filter):
        return await self.collection.count_documents(filter)

    async def _query(self, skip, limit, filter, sort_by):
        return await self.collection.find(filter).sort(
            sort_by).skip(skip).limit(limit).to_list(limit)

    def init_table(self):
        self.collection = self.config.tests.data1_collection
        args = dict(
            length=self._length,
            query=self._query,
            column=COLS,
            fixed_header=self.get_argument("fixed_header", bool, default=True),
            hide_header=self.get_argument("hide_header", bool, default=False),
            multi_sort=True,
            height=None,
            dense=self.get_argument("dense", bool, default=True),
            select=False,
            multi_select=False,
            search=True,
            per_page=self.get_argument("per_page", int, default=10),
            page=self.get_argument("page", int, default=0),
            filter=self.get_argument("filter", dict, default=None,
                                     dict_decode=convert),
            sort_by=self.get_argument("sort", list, default=None)
        )
        return CoreDataTable(**args)

    async def post(self):
        datatable = self.init_table()
        self.reply(
            await datatable.post()
        )

    async def get(self):
        datatable = self.init_table()
        self.reply(
            await datatable.get()
        )


class TableServer1(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/table", TableHandler)
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
