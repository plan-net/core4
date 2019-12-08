import datetime
import random

import pymongo

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.tool.datatable import CoreDataTableRequest


def make_data(count):
    mongo = pymongo.MongoClient("mongodb://core:654321@localhost:27017")
    coll = mongo.core4test.data1
    if coll.count_documents({}) == 0:
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


COLS = [
    {
        "name": "_id",
        "key": True,
        "hide": True,
        "editable": False
    },
    {
        "name": "idx",
        "label": "#",
        "format": "{:05d}"
    },
    {
        "name": "segment",
        "label": "Segment",
        "format": "{:s}"
    },
    {
        "name": "real",
        "label": "Realzahl",
        "format": "{:+1.3f}"
    },
    {
        "name": "value",
        "label": "Ganzzahl",
        "format": "{:d}"
    },
    {
        "name": "timestamp",
        "label": "Zeitstempel",
        "format": "{:%d.%m.%Y at %H:%M:%S}"
    }
]


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


class TableServer(CoreApiContainer):
    rules = [
        ("/table", TableHandler)
    ]


if __name__ == '__main__':
    # create test data
    make_data(10000)

    # change default database
    import os

    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
    from core4.api.v1.tool.functool import serve

    # start server including core4 standard API
    serve(TableServer)

