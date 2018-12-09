from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager


class RouteHandler(CoreRequestHandler):
    title = "core4 api/widget endpoint collection"
    author = "mra"

    async def get(self):
        collection = self.config.sys.handler.connect_async()
        data = []

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        query_filter = self.get_argument("filter", as_type=dict, default=None)
        sort_by = self.get_argument("sort", default="_id")
        sort_order = self.get_argument("order", default=1)

        if query_filter:
            f = {"$and": [
                {"visited": {"$ne": None}},
                query_filter
            ]}
        else:
            f = {"visited": {"$ne": None}}

        async for doc in collection.find(f).sort("rule_id", 1):
            if await self.user.has_api_access(doc["qual_name"]):
                data.append(doc)

        async def _length(filter):
            return len(data)

        async def _query(skip, limit, filter, sort_by):
            return data[skip:skip + limit]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query,
                          sort_by=[sort_by, int(sort_order)],
                          filter=query_filter)
        self.reply(await pager.page())
