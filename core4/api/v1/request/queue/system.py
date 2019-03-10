import core4.const
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.query import QueryMixin


# todo: requires documentation
class SystemHandler(CoreRequestHandler, QueryMixin):
    """
    Retrieves system state, i.e.

    * alive time of workers, scheduler and app nodes
    * maintenance modes (global and project specific)
    """
    author = "mra"
    title = "system information"

    async def get(self):
        """
        Methods:
            GET /system

        Parameters:
            none

        Returns:
            data element with

            - **alive** (list): of alive worker, scheduler and app nodes
            - **maintenance** (dict): the global maintenance mode (``True`` or
              ``False``) and the list of projects in maintenance

        Raises:
            401: Unauthorized
            403: Forbidden

        Examples:
            >>> from requests import get
            >>> signin = get("http://devops:5001/core4/api/login?username=admin&password=hans")
            >>> signin
            <Response [200]>
            >>> rv = get("http://devops:5001/core4/api/v1/system?token=" + signin.json()["data"]["token"])
            >>> rv
            <Response [200]>
            >>> rv.json()
            {'_id': '5c854813ad70717b3aaa077a',
             'code': 200,
             'data': {'alive': [{'_id': 'app@devops',
                'heartbeat': 5.0,
                'hostname': 'devops',
                'kind': 'app',
                'loop': '2019-03-10T17:22:11',
                'loop_time': 80.0,
                'pid': 31546,
                'port': 5001,
                'protocol': 'http'},
               {'_id': 'scheduler@devops',
                'heartbeat': None,
                'hostname': 'devops',
                'kind': 'scheduler',
                'loop': None,
                'loop_time': None,
                'pid': 6474}],
              'maintenance': {'project': ['client1'], 'system': False}},
             'message': 'OK',
             'timestamp': '2019-03-10T17:23:31.576754'}
        """

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
        return await self.config.sys.worker.count_documents(
            {"_id": "__maintenance__"}) > 0

    async def _project_maintenance(self):
        doc = await self.config.sys.worker.find_one({"_id": "__project__"})
        if doc:
            return doc["maintenance"]
        return []
