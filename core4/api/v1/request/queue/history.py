#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import datetime
from dateutil.relativedelta import *

import core4.const
import core4.util.tool

from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager

dates = ['year', 'month', 'day', 'hour', 'minute', 'second']
date_format = "%Y-%m-%dT%H:%M:%S"
default_days = 7


class JobHistoryHandler(CoreRequestHandler):
    """
    Retrieves the paginated job state history from ``sys.event``. This provides
    total and aggregated job counts with the following dimensions:

    * job qual_name
    * job state
    * job flags non-stopper, zombie, killed and removed
    """
    author = "mra"
    title = "job queue history"

    async def get(self):
        """
        Methods:
            GET /jobs/history

        Parameters:
            per_page (int): number of jobs per page
            page (int): requested page (starts counting with ``0``)
            filter (dict): optional mongodb filter
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
            >>> rv = get("http://devops:5001/core4/api/v1/jobs/history?token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/jobs/history?page=1&token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/jobs/history?sort=1&token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
        """

        per_page = self.get_argument("per_page", as_type=int, default=10)
        current_page = self.get_argument("page", as_type=int, default=0)
        query_filter = self.get_argument("filter",
                                         as_type=dict,
                                         default={},
                                         dict_decode=self.dict_decode)
        sort = self.get_argument("sort", as_type=int, default=-1)
        coll = self.config.sys.event
        query = {
            "channel": core4.const.QUEUE_CHANNEL
        }
        if query_filter:
            query.update(query_filter)

        async def _length(filter):
            return await coll.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            cur = coll.find(
                filter,
                projection={"created": 1, "data": 1, "_id": 0}
            ).sort(
                [("$natural", sort)]
            ).skip(
                skip
            ).limit(
                limit
            )
            ret = []
            for doc in await cur.to_list(length=limit):
                total = sum([v for v in doc["data"]["queue"].values()])
                doc["data"]["queue"]["created"] = doc["created"]
                doc["data"]["queue"]["total"] = total
                ret.append(doc["data"]["queue"])
            return ret

        pager = CorePager(per_page=per_page,
                          current_page=current_page,
                          length=_length, query=_query,
                          filter=query)
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


class ComocoHistoryHandler(CoreRequestHandler):
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
            start_date (str): start date for mongoDB $gte query
            end_data (str): end date for mongoDB $lte query
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
        sort = self.get_argument("sort",
                                 as_type=int,
                                 default=-1)

        per_page = self.get_argument("per_page",
                                     as_type=int,
                                     default=10)

        current_page = self.get_argument("page",
                                         as_type=int,
                                         default=0)

        start_date = self.get_argument("startDate",
                                       as_type=str,
                                       default=self._default_start_date())

        end_date = self.get_argument("endDate",
                                     as_type=str,
                                     default=None)

        coll = self.config.sys.event
        query = {
            "channel": core4.const.QUEUE_CHANNEL
        }

        group_by_date_time_period = self._group_by(start_date, end_date)

        query.update(self._between(start_date, end_date))

        async def _length(filter):
            cur = coll.aggregate([
                {
                    "$match": filter
                },
                {
                    "$project": {
                        "_id": 0,
                        "created": "$created"
                    }
                },
                {
                    "$group": {
                        "_id": group_by_date_time_period
                    }
                },
                {
                    "$sort": {"record.created": sort}
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
                    "$match": filter
                },
                {
                    "$project": {
                        "_id": 0,
                        "queue": "$data.queue",
                        "created": "$created",
                        "total": {
                            "$sum": [
                                "$data.queue.pending",
                                "$data.queue.deferred",
                                "$data.queue.failed",
                                "$data.queue.running",
                                "$data.queue.error",
                                "$data.queue.inactive",
                                "$data.queue.killed"
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": group_by_date_time_period,
                        "total": {"$max": "$total"},
                        "points": {"$push": "$$ROOT"},
                        "count": {"$sum": 1}
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

    @classmethod
    def _group_by(cls, start, end=None):
        """

        Parameters:
            start (str): - start date
            end (str| None): - end date

        Returns:
            full mongoDB _id query for $group

        Examples:
            {
                'year':  {'$year': '$created'},
                'month': {'$month': '$created'},
                'day':   {'$dayOfMonth': '$created'},
                'hour': {
                    '$subtract': [
                        {'$hour': '$created'},
                        {'$mod': [{'$hour': '$created'}, 1]}
                    ]
            }
            --------------------------------------------------------
            {
                'year':  {'$year': '$created'},
                'month': {'$month': '$created'},
                'day':   {
                    '$subtract': [
                        {'$dayOfMonth': '$created'},
                        {'$mod': [{'$dayOfMonth': '$created'}, 1]}
                    ]
                }
            }
        """
        grouping_id = {}
        start_date = datetime.datetime.strptime(start, date_format)

        if end:
            end_date = datetime.datetime.strptime(end, date_format)
        else:
            end_date = datetime.datetime.now()

        precision = {
            "year": {
                "divisor": "day", # day
                "remainder": 1
            },
            "month": {
                "divisor": "hour", # hour
                "remainder": 1
            },
            "day": {
                "divisor": "minute", # minute
                "remainder": 1
            },
            "hour": {
                "divisor": "second", # second
                "remainder": 1
            },
            "minute": {
                "divisor": "second",
                "remainder": 1
            },
            "second": {
                "divisor": "millisecond",
                "remainder": 1
            }
        }

        period = precision[
            cls._get_period(start_date, end_date)["delta"]
        ]

        for date in dates:
            needed_period = period["divisor"]
            if date == needed_period:
                grouping_id[needed_period] = cls._subtract_template(
                    needed_period,
                    period["remainder"]
                )

                break
            else:
                grouping_id[date] = {cls._adapt_day(date): "$created"}

        return grouping_id

    @classmethod
    def _get_period(cls, start, end):
        """
        Calculate delta between 2 dates

        Parameters:
            start (datetime): - start date
            end (datetime| None): - end date

        Returns:
            info about the difference between start date and end date

        Examples:
            {
                "delta": "month",
                "amount": 2
            }
            ---------------------------------------------------------
            {
                "delta": "hour",
                "amount": 9
            }
        """
        rdelta = relativedelta(end, start)
        period = {
            "delta": "second",
            "amount": 1
        }

        for date in dates:
            amount = rdelta.__getattribute__((date + "s"))
            if amount > 0:
                period["delta"] = date
                period["amount"] = amount
                break

        return period

    @classmethod
    def _subtract_template(cls, name, amount):
        """
        Build mongoDB subtract query depend on period

        Parameters:
            name (str): - period name: year, month, day, hour, minute, second
            amount (int): - precision: every 1 day | hour | minute,
                                       every 5 day | hour | minute,
                                       ...
                                       every n day | hour | minute

        Returns:
            mongoDB $subtract query

        Examples:
            {
                "$subtract": [
                    {"$dayOfMonth": "$created"},
                    {"$mod": [{"$dayOfMonth": "$created"}, 1]}
                ]
            }
            --------------------------------------------------------
            {
                "$subtract": [
                    {"$minute": "$created"},
                    {"$mod": [{"$minute": "$created"}, 1]}
                ]
            }

        """
        period = cls._adapt_day(name)

        return {
            "$subtract": [
                {period: "$created"},
                {"$mod": [{period: "$created"}, amount]}
            ]
        }

    @classmethod
    def _adapt_day(cls, name):
        """
        Get mongoDB operator for some period

        Parameters:
            name (str): period name: year, month, day, hour, minute, second

        Returns:
            build mongoDB operator base on fn argument,
            special case "day" which should be represent like "dayOfMonth"

        Examples:
            "$year"
            --------------------------------------------------------
            "$dayOfMonth"

       """
        return '$dayOfMonth' if name == 'day' else ("$" + name)

    @classmethod
    def _between(cls, start_date, end_date=None):
        """
        Build mongoDB query for getting documents for some datetime range

        Parameters:
            start_date (str): start date for mongoDB query
            end_date (str| None): end date for mongoDB query

        Returns:
            mongoDB $match query

            - **$gle** (datetime): - mongoDB query for getting all documents
                                     which greater than or equivalent this date

            - **$lte** (datetime): - mongoDB query for getting all documents
                                     which less than or equivalent this date

        Examples:
            {
                "created": {
                    "$gte": 2019-04-13T09:48:23
                }
            }
            --------------------------------------------------------
            {
                "created": {
                    "$gte": 2019-04-13T09:48:23,
                    "$lte": 2019-06-12T14:32:18
                }
            }

        """
        match = {
            "created": {
                "$gte": datetime.datetime.strptime(start_date, date_format)
            }
        }

        if end_date:
            match["created"].update({
                "$lte": datetime.datetime.strptime(end_date, date_format)
            })

        return match

    @classmethod
    def _default_start_date(cls):
        """
        Get date (currently) for 7 days past

        Parameters:

        Returns:
            string representation of the date (default days past)

        Examples:
            "2019-04-13T09:48:23"

        """
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=default_days)

        return week_ago.strftime(date_format)


