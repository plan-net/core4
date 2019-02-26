#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements core4 standard :class:`RouteHandler` delivering core4 API/endpoint
collection.
"""
from bson.son import SON
from core4.const import ENTER_URL, HELP_URL, CARD_URL
from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.query import QueryMixin
from core4.util.pager import CorePager


class RouteHandler(CoreRequestHandler, QueryMixin):
    title = "core4 api/widget endpoint collection"
    author = "mra"

    async def get(self):
        """
        Retrieve API endpoint collection across all http servers.

        Methods:
            GET /info - API endpoint listing

        Parameters:
            json (bool): retrieve JSON format, defaults to ``False`` (HTML)
            per_page (int): number of elements per page
            page (int): requested page (start counting with 0)
            filter (dict): MongoDB query filter
            sort (list of tuple): with key and sort order
            content_type (str): force json, html, text

        Returns:
            collection (list) of dict with

            - **_id** (:class:`bson.objectid.ObjectId`): MonboDB identifier
            - **endpoint** (*list* of *dict*)

              - **pattern** (*regular expression*): endpoint matching criteria
              - **card_url** (*str*): full url to the card page view
              - **enter_url** (*str*): full url to the handler entry
              - **help_url** (*str*): full url to the help page
              - **routing** (*str*): url prefix with protocol and domain
                adressing the serving container

            - **project** (*str*): name
            - **qual_name** (*str*): of the :class:`.CoreRequestHandler`
            - **route_id** (*str*): MD5 digest of the route
            - **tag** (*list*): of tag lables assigned to the
              :class:`.CoreRequestHandler`
            - **title** (*str*): of the :class:`.CoreRequestHandler`

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get("http://localhost:5001/core4/api/info?per_page=2", headers=h)
            >>> rv.json()
        """

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        query = self.get_argument("filter", as_type=dict, default=None)
        sort_by = self.get_argument("sort", as_type=list,
                                    default=[
                                        ("qual_name", 1), ("route_id", 1)])
        filter_by = [{"started_at": {"$ne": None}}]
        if query is not None:
            filter_by.append(query)
        coll = self.config.sys.handler.connect_async()

        pipeline = [
            {
                "$match": {"$and": filter_by}
            },
            {
                "$sort": SON(sort_by)
            },
            {
                "$project": {
                    "project": 1,
                    "tag": 1,
                    "route_id": 1,
                    "routing": 1,
                    "qual_name": 1,
                    "title": 1,
                    "pattern": 1
                }
            },

        ]
        nodes = ["{}://{}:{}".format(n["protocol"], n["hostname"], n["port"])
                 for n in self.get_daemon(kind="app")]
        data = []
        seen = {}

        def _endpoint(edoc):
            pattern = edoc.pop("pattern")
            routing = edoc.pop("routing")
            return {
                "help_url": routing + HELP_URL + "/" + edoc["route_id"],
                "enter_url": routing + ENTER_URL + "/" + edoc["route_id"],
                "card_url": routing + CARD_URL + "/" + edoc["route_id"],
                "pattern": pattern,
                "routing": routing
            }

        async for doc in coll.aggregate(pipeline):
            if await self.user.has_api_access(doc["qual_name"]):
                if doc["routing"] in nodes:
                    if doc["route_id"] not in seen:
                        doc["endpoint"] = [_endpoint(doc)]
                        data.append(doc)
                        seen[doc["route_id"]] = data[-1]["endpoint"]
                    else:
                        seen[doc["route_id"]].append(_endpoint(doc))

        async def _length(**_):
            return len(data)

        async def _query(skip, limit, *_, **__):
            return data[skip:skip + limit]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query)
        page = await pager.page()
        if self.wants_html():
            return self.render("template/route.html", page=page)
        self.reply(page)
