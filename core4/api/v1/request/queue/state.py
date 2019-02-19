#This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tornado import gen
from tornado.iostream import StreamClosedError

from core4.api.v1.request.main import CoreRequestHandler
from core4.base import CoreBase
from core4.util.data import json_encode

QUERY_SLEEP = 1.
PUBLISH_SLEEP = 0.5


class QueueStatus(CoreBase):
    """
    Continuously query ``sys.stat`` for changes. Collection ``sys.stat``
    tracks all changes in ``sys.queue``.

    A :class:`QueueStatus`` instance is created at startup, see
    :mod:`core4.api.v1.server`.
    """

    def __init__(self):
        super().__init__()
        self.data = None

    async def update(self):
        """
        Delivers a sparse dict with ``timestamp`` and the number of jobs in
        state ````pending``, ``deferred``, ``failed``, ``running``, ``killed``,
        ``error`` or ``inactive``.
        """
        sys_stat = self.config.sys.stat.connect_async()
        cur = sys_stat.find(projection={"_id": 0}).sort(
            "timestamp", -1).limit(1)
        doc = await cur.to_list(length=1)
        if doc:
            last = doc[-1]["timestamp"]
            self.data = doc
        else:
            last = None
        while True:
            nxt = gen.sleep(QUERY_SLEEP)
            update = []
            if last:
                f = {"timestamp": {"$gt": last}}
            else:
                f = {}
            cursor = sys_stat.find(
                filter=f, projection={"_id": 0}).sort("timestamp", 1)
            async for doc in cursor:
                update.append(doc)
                last = doc["timestamp"]
            if update:
                self.data = update
            await nxt


class QueueHandler(CoreRequestHandler):
    """
    State stream of ``sys.stat``. The endpoint delivers a
    ``text/event-stream`` content type with continuous updates of
    collection ``sys.stat``. The stream with the latest state and delivers
    updates in JSON format whenever new records arrive in ``sys.stat``.
    """

    author = "mra"
    title = "queue state stream"
    tag = ["job management"]

    def initialize(self, source):
        """
        Initialises the ``text/event-stream``

        :param source: data source to watch and deliver (:class:`.QueueStatus`)
        """
        self.source = source

    async def _publish(self, data):
        # internal method to stream data from QueueStatus object
        try:
            bytes = 0
            if data:
                for doc in data:
                    js = json_encode(doc, indent=None, separators=(',', ':'))
                    self.write(js + "\n\n")
                    bytes += len(js)
                self.logger.info("serving [%s] with [%d] records, [%d] byte",
                                 self.current_user, len(data), bytes)
                f = self.flush()
                await f
        except StreamClosedError:
            self.logger.info("stream closed")
            self.exit = True
        except Exception:
            self.logger.error("stream error", exc_info=True)
            self.exit = True

    async def get(self):
        """
        Methods:
            GET / - stream ``sys.stat``

        Parameters:
            None

        Returns:
            stream of dict with

            - **timestamp** (*float*): epoch seconds since 1970 (unix date)
            - **pending** (*int*): number of jobs in state *pending*
            - **deferred** (*int*): number of jobs in state *deferred*
            - **failed** (*int*): number of jobs in state *failed*
            - **running** (*int*): number of jobs in state *running*
            - **killed** (*int*): number of jobs in state *killed*
            - **error** (*int*): number of jobs in state *error*
            - **inactive** (*int*): number of jobs in state *inactive*

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>>
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> auth = {"username": "admin", "password": "hans"}
            >>> signin = post(url + "/login", json=auth)
            >>> token = signin.json()["data"]["token"]
            >>>
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get(url + "/queue", headers=h, stream=True)
            >>> rv
            <Response [200]>
            >>>
            >>> for line in rv.iter_lines():
            >>>     if line:
            >>>         ret = json.loads(line.decode("utf-8"))
            >>>         print(ret)
            {'timestamp': 1541017444.365525, 'killed': 1}
            {'pending': 1, 'timestamp': 1541017550.765429, 'killed': 1}
            {'running': 1, 'timestamp': 1541017556.893435, 'killed': 1}
            {'timestamp': 1541017567.382534, 'killed': 1}
        """
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.exit = False
        await self._publish(self.source.data)
        last = self.source.data
        while not self.exit:
            if self.source.data != last:
                await self._publish(self.source.data)
                last = self.source.data
            await gen.sleep(PUBLISH_SLEEP)
        self.finish()
