#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import core4.const
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager


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
            >>> signin = get("http://devops:5001/core4/api/login?username=admin&password=hans")
            >>> signin
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/jobs/history?token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/jobs/history?page=1&token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
        """

        per_page = self.get_argument("per_page", as_type=int, default=10)
        current_page = self.get_argument("page", as_type=int, default=0)
        query_filter = self.get_argument("filter", as_type=dict, default={})
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
                [("$natural", -1)]
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
