import core4.const
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.query import QueryMixin


# todo: requires documentation
class SystemHandler(CoreRequestHandler, QueryMixin):
    """
    Retrieves system state, i.e.

    * alive time of workers, scheduler and app nodes
    * maintenance mode (global and project specific)
    """
    author = "mra"
    title = "system information"

    # def initialise_object(self):
    #     self.sys_worker = self.config.sys.worker

    async def get(self):
        return self.reply({
            "alive": await self._get_daemon(),
            "maintenance": {
                "system": await self._maintenance(),
                "project": await self._project_maintenance()
            }
        })

    async def _get_daemon(self):
        cur = self.config.sys.worker.aggregate(self.pipeline_daemon())
        data = []

        def delta2sec(t):
            return (core4.util.node.mongo_now()
                    - t.replace(microsecond=0)).total_seconds()

        async for doc in cur:
            if doc["heartbeat"]:
                doc["heartbeat"] = delta2sec(doc["heartbeat"])
            if doc.get("loop", None):
                doc["loop_time"] = delta2sec(doc["loop"])
            else:
                doc["loop_time"] = None
                doc["loop"] = None
            data.append(doc)
        return data

    async def _maintenance(self):
        return await self.sys_worker.count_documents(
            {"_id": "__maintenance__"}) > 0

    async def _project_maintenance(self):
        doc = await self.sys_worker.find_one({"_id": "__project__"})
        if doc:
            return doc["maintenance"]
        return []
