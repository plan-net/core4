from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager
import core4.const


# todo: requires documentation
class JobHistoryHandler(CoreRequestHandler):
    """
    Retrieves the paginated job state history from ``sys.event``.
    """
    author = "mra"
    title = "job queue history"

    async def get(self):
        per_page=self.get_argument("per_page", as_type=int, default=10)
        current_page=self.get_argument("page", as_type=int, default=0)
        query_filter=self.get_argument("filter", as_type=dict, default={})
        coll = self.config.sys.event.connect_async()
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
        Same as :meth:`.get`.
        """
        return self.get()