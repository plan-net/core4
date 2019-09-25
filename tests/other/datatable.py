import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.server import CoreApiServer
from tests.api.test_test import setup, mongodb, run
from core4.data.table import CoreDataTable
from  core4.util.pager import CorePager
import datetime
import bson.objectid

import random

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

    async def get(self, path):

        coll = self.config.tests.data1_collection

        async def _length(filter):
            return await coll.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            return await coll.find(filter).sort(sort_by).skip(skip).limit(
                limit).to_list(limit)

        def _hook(obj):
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

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        sort_by = self.get_argument("sort", as_type=list, default=[['segment', 1]])
        filter = self.get_argument("filter", as_type=dict, default={}, dict_decode=_hook)

        table = CoreDataTable(
            "table1/data",
            height="320px",
            column=[
                {"name": "timestamp", "title": "Timestamp", "format": "{:%d.%m.%Y %H:%M:%S}", "visible": True, "align": "center"},
                {"name": "_id", "title": "ID", "format": "{:}", "visible": True, "align": "left"},
                {"name": "idx", "title": "INDEX", "format": "- {:d} -", "visible": True, "align": "center"},
                {"name": "segment", "title": "GRUPPE", "format": "{:s}", "visible": True, "align": "right"},
                {"name": "real", "title": "ZAHL", "format": "{:1.4f} €", "visible": True, "align": "right"},
                {"name": "value", "title": "GANZZAHL", "format": "{:012d}", "visible": True, "align": "left"}
            ],
            per_page=per_page,
            current_page=current_page,
            length=_length,
            query=_query,
            sort_by=sort_by,
            filter=filter,
        )

        if path == "":
            self.render(
                "table/table1.html",
                dt=table,
            )
        elif path == "/data":
            self.reply(await table.page())


class TableServer1(CoreApiContainer):
    root = "/test"
    rules = [
        (r"/table1(.*)", TableHandler1)
    ]


if __name__ == '__main__':
    import pymongo
    mongo = pymongo.MongoClient("mongodb://core:654321@localhost:27017")
    make_data(mongo.core4test.data1, 1000)

    import os
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
    from core4.api.v1.tool.functool import serve
    serve(TableServer1)