from tornado import gen
from tornado.iostream import StreamClosedError

from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.util import json_encode
from core4.base import CoreBase

QUERY_SLEEP = 1.
PUBLISH_SLEEP = 0.5


class QueueStatus(CoreBase):
    """Generic object for producing data to feed to clients."""

    def __init__(self):
        super().__init__()
        self.data = None
        self.sys_stat = self.config.sys.stat.connect_async()

    async def update(self):
        cur = self.sys_stat.find().sort("_id", -1).limit(1)
        doc = await cur.to_list(length=1)
        if doc:
            last = doc[-1]["_id"]
            self.data = doc
            self.logger.debug("got initial %s", self.data)
        else:
            last = None
        while True:
            nxt = gen.sleep(QUERY_SLEEP)
            update = []
            cursor = self.sys_stat.find(
                {"_id": {"$gt": last}}).sort("_id", 1)
            async for doc in cursor:
                update.append(doc)
            if update:
                self.logger.debug("%s got %s", last, update)
                last = update[-1]["_id"]
                self.data = update
            await nxt

class QueueHandler(CoreRequestHandler):

    def initialize(self, source):
        self.source = source
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.exit = False

    async def publish(self, data):
        try:
            for doc in data:
                js = json_encode(doc, indent=None, separators=(',', ':'))
                self.write(js + "\n\n")
            self.logger.info("serving [%s] with [%d] records, [%d] byte",
                             self.current_user, len(data), len(js))
            f = self.flush()
            await f
        except StreamClosedError:
            self.logger.info("stream closed")
            self.exit = True
        except:
            self.logger.error("stream error")
            self.exit = True

    async def get(self):
        await self.publish(self.source.data)
        last = self.source.data
        while not self.exit:
            if self.source.data != last:
                await self.publish(self.source.data)
                last = self.source.data
            await gen.sleep(PUBLISH_SLEEP)
        self.finish()
