from tornado import gen
from tornado.ioloop import PeriodicCallback
from tornado.iostream import StreamClosedError

from core4.api.v1.application import CoreApiContainer, serve
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.util import json_encode
from core4.base.main import CoreBase


class QueueStatus(CoreBase):
    """Generic object for producing data to feed to clients."""

    def __init__(self):
        super().__init__()
        self._gen = self.get_stat()
        self.data = None

    def get_stat(self):
        doc = self.config.sys.stat.find_one(
            sort=[("_id", -1)], projection=["_id"])
        if doc is None:
            last = None
        else:
            last = doc["_id"]
        while True:
            update = list(self.config.sys.stat.find(
                {"_id": {"$gt": last}}, sort=[("_id", 1)]))
            if update:
                last = update[-1]["_id"]
            yield update

    def update(self):
        self.data = next(self._gen)


class EventSource(CoreRequestHandler):
    """Basic handler for server-sent events."""

    def initialize(self, source):
        """The ``source`` parameter is a string that is updated with
        new data. The :class:`EventSouce` instance will continuously
        check if it is updated and publish to clients when it is.

        """
        self.source = source
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.exit = False

    async def publish(self, data):
        """Pushes data to a listener."""
        try:
            js = json_encode(data, indent=None, separators=(',', ':')) + "\n"
            self.write(js)
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
        step = self.publish(self.source.data)
        await step
        while not self.exit:
            if self.source.data:
                step = self.publish(self.source.data)
                await step
            await gen.sleep(1)
        self.finish()


publisher = QueueStatus()


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
        (r'/events', EventSource, dict(source=publisher))
    ]


if __name__ == '__main__':
    queue_state = PeriodicCallback(lambda: publisher.update(), 1000.)
    queue_state.start()
    serve(CoreApiServer)
