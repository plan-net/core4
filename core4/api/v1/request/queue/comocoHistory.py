#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import datetime

import core4.const
import core4.util.tool
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager


class ComocoHistory(CoreRequestHandler):
    """
    Retrieves the paginated job state history from ``sys.event``. This provides
    total and aggregated job counts with the following dimensions:

    * job state
    * job flags non-stopper, zombie, killed and removed
    """
    author = "oto"
    title = "comoco history"

    async def get(self):
        """
        Methods:
            GET /comoco/history


        Parameters:
            per_page (int): number of jobs per page
            current_page (int): requested page (starts counting with ``0``)
            query_filter (dict): optional mongodb filter
            sort (str): 1 - for ascending sorting,
                        -1 - for descending sorting
                        by default -1 (desc) sorting

        Returns:
            data element with list of aggregated job counts For pagination the
            following top level attributes are returned:

            - **total_count** (int): the total number of records
            - **count** (int): the number of records in current page
            - **page** (int): current page (starts counting with ``0``)
            - **page_count** (int): the total number of pages
            - **per_page** (int): the number of elements per page

        Raises:
            401: Unauthorized
            403: Forbidden

        Examples:
            >>> from requests import get
            >>> signin = get("http://devops:5001/core4/api/v1/login?username=admin&password=hans")
            >>> signin
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/comoco/history?token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/comoco/history?page=1&token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/comoco/history?sort=1&token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>

        """
        coll = self.config.sys.event
        sort = self.get_argument("sort", as_type=int, default=-1)
        per_page = self.get_argument("per_page", as_type=int, default=10)
        current_page = self.get_argument("page", as_type=int, default=0)
        query_filter = self.get_argument("filter",
                                         as_type=dict,
                                         default={},
                                         dict_decode=self.dict_decode)
        query = {
            "channel": core4.const.QUEUE_CHANNEL  # ToDo: rename the channel
        }

        if query_filter:
            query.update(query_filter)

        async def _length(filter):
            cur = coll.aggregate([
                {
                    "$sort": {"created": sort}
                },
                {
                    "$match": filter
                },
                {
                    "$project": {
                        "_id": 0,
                        "created": "$created",
                        "datetime": {
                            "minute": {"$minute": "$created"},
                            "hour":   {"$hour": "$created"},
                            "day":    {"$dayOfMonth": "$created"},
                            "month":  {"$month": "$created"},
                            "year":   {"$year": "$created"}
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "minute": "$datetime.minute",
                            "hour":   "$datetime.hour",
                            "day":    "$datetime.day",
                            "month":  "$datetime.month",
                            "year":   "$datetime.year"
                        }
                    }
                },
                {
                    "$count": "passing_scores"
                }
            ])

            result = 0

            for doc in await cur.to_list(length=1):
                result = doc["passing_scores"]

            return result

        async def _query(skip, limit, filter, sort_by):
            pipeline = [
                {
                    "$sort": {"created": sort}
                },
                {
                    "$match": filter
                },
                {
                    "$project": {
                        "_id": 0,
                        "queue": "$data.queue",
                        "created": "$created",
                        "total": {"$sum": [
                            "$data.queue.pending",
                            "$data.queue.deferred",
                            "$data.queue.failed",
                            "$data.queue.running",
                            "$data.queue.error",
                            "$data.queue.inactive",
                            "$data.queue.killed"
                        ]
                        },
                        "datetime": {
                            "minute": {"$minute": "$created"},
                            "hour":   {"$hour": "$created"},
                            "day":    {"$dayOfMonth": "$created"},
                            "month":  {"$month": "$created"},
                            "year":   {"$year": "$created"}
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "minute": "$datetime.minute",
                            "hour":   "$datetime.hour",
                            "day":    "$datetime.day",
                            "month":  "$datetime.month",
                            "year":   "$datetime.year"
                        },
                        "total": {"$max": "$total"},
                        "points": {"$push": "$$ROOT"}
                    }
                },
                {
                    "$project": {
                        "_id": "$_id",
                        "total": "$total",
                        "points": {
                            "$setDifference": [{
                                "$map": {
                                    "input": "$points",
                                    "as": "point",
                                    "in": {
                                        "$cond": [
                                            {"$eq": ["$total",
                                                     "$$point.total"]},
                                            "$$point",
                                            "false"
                                        ]
                                    }

                                }
                            },
                                ["false"]
                            ]
                        }
                    }
                },
                {
                    "$unwind": "$points"
                },
                {
                    "$group": {
                        "_id": "$_id",
                        "total": {"$max": "$total"},
                        "record": {"$first": "$points"}
                    }
                },
                {
                    "$sort": {"record.created": sort}
                },
                {
                    "$skip": skip
                },
                {
                    "$limit": limit
                }
            ]

            cur = coll.aggregate(pipeline)

            ret = []

            for doc in await cur.to_list(length=1000):
                ret_doc = {
                    "created": doc["record"]["created"],
                    "total": doc["record"]["total"]
                }

                ret.append(
                    core4.util.tool.dict_merge(
                        ret_doc, doc["record"]["queue"]
                    )
                )

            return ret

        pager = CorePager(
            per_page=per_page,
            current_page=current_page,
            length=_length,
            query=_query,
            filter=query
        )

        page = await pager.page()

        return self.reply(page)


    async def post(self):
        """
        Same as :meth:`get`.
        """
        return self.get()

    def dict_decode(self, dct):
        """
        Hook for json_decode function for custom formatting dictionary

        :param dct: dictionary for parse
        :return: formatted dictionary
        """
        for k, v in dct.items():

            # recursively check dict
            if isinstance(v, dict):
                try:
                    dct[k] = self.dict_decode(dct[k])
                except:
                    pass

            # if value is date string then convert this value
            # into python datetime format for mongoDB querying
            if isinstance(v, str):
                try:
                    dct[k] = datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
                except:
                    pass

        return dct

