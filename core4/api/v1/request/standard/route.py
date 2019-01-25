import core4.const
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager


class RouteHandler(CoreRequestHandler):
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

            - **_id** (*:class:`bson.objectid.ObjectId`*): MonboDB identifier
            - **card_url** (*str*): full url to the card page view
            - **help_url** (*str*): full url to the help page
            - **project** (*str*): name
            - **qual_name** (*str*): of the :class:`.CoreRequestHandler`
            - **route_id** (*str*): MD5 digest of the route
            - **routine** (*str*): url prefix with protocol and domain
              adressing the serving container
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
            >>> rv = get("http://localhost:5001/core4/api/v1/info?per_page=2", headers=h)
            >>> rv.json()
        """

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        query = self.get_argument("filter", as_type=dict, default=None)
        sort_by = self.get_argument("sort", as_type=dict,
                                    default={"qual_name": 1, "route_id": 1})

        filter_by = [{"started_at": {"$ne": None}}]
        if query is not None:
            filter_by.append(query)
        coll = self.config.sys.handler.connect_async()
        data = []

        pipeline = [
            {
                "$match": {"$and": filter_by}
            },
            {
                "$sort": sort_by
            },
            {
                "$project": {
                    "project": 1,
                    "tag": 1,
                    "route_id": 1,
                    "routing": 1,
                    "qual_name": 1,
                    "title": 1
                }
            },
            {
                "$group": {
                    "_id": "$route_id",
                    "project": {"$first": "$project"},
                    "tag": {"$first": "$tag"},
                    "routing": {"$first": "$routing"},
                    "qual_name": {"$first": "$qual_name"},
                    "title": {"$first": "$title"},
                }
            },
            {
                "$project": {
                    "route_id": "$_id",
                    "project": "$project",
                    "tag": "$tag",
                    "routing": "$routing",
                    "qual_name": "$qual_name",
                    "title": "$title",

                }
            }

        ]

        async for doc in coll.aggregate(pipeline):
            if await self.user.has_api_access(doc["qual_name"]):
                doc["help_url"] = doc["routing"] \
                                  + core4.const.HELP_URL \
                                  + "/" + doc["route_id"]
                doc["enter_url"] = doc["routing"] \
                                   + core4.const.ENTER_URL \
                                   + "/" + doc["route_id"]
                doc["card_url"] = doc["routing"] \
                                  + core4.const.CARD_URL \
                                  + "/" + doc["route_id"]
                data.append(doc)

        async def _length(filter):
            return len(data)

        async def _query(skip, limit, filter, sort_by):
            return data[skip:skip + limit]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query)
        page = await pager.page()
        if self.wants_html():
            return self.render("template/route.html", page=page)
        self.reply(page)
