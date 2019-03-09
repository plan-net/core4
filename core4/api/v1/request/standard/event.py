from tornado import gen

import core4.const
import core4.util.node
from core4.api.v1.request.websocket import CoreWebSocketHandler
from core4.base.main import CoreBase
from core4.queue.query import QueryMixin
from core4.util.data import json_encode, json_decode


# todo: permission design ... OK
# todo: sticky messages
# todo: personal messages ... denied
# todo: queue history endpoint ... OK
# todo: message history including sticky notes
# todo: unstick sticky notes
# todo: maintenance info ... OK


class EventWatch(CoreBase):
    """
    Watches collection ``sys.event`` for any changes using MongoDB _watch_
    feature. All changes are forwarded to :class:`.EventHandler` using
    :meth:`on_event <.EventHandler.on_event>` method.
    """

    async def watch(self):
        coll = self.config.sys.event.connect_async()
        async with coll.watch() as change_stream:
            async for change in change_stream:
                EventHandler.on_event(change)


class QueueWatch(CoreBase, QueryMixin):
    """
    Continuously queries ``sys.queue`` and forwards to :class:`.EventHandler`
    using :meth:`on_queue <.EventHandler.on_queue>` method.
    """

    async def watch(self):
        coll = self.config.sys.queue.connect_async()
        pipeline = self.pipeline_queue_state()
        interval = self.config.event.queue_interval
        while True:
            nxt = gen.sleep(interval)
            cursor = coll.aggregate(pipeline)
            data = []
            async for doc in cursor:
                data.append(doc)
            await EventHandler.on_queue(data)
            await nxt


class EventHandler(CoreWebSocketHandler):
    """
    Web socket handler to process channel interests and to deliver

    # chat messages on channel _message_
    # job events from ``sys.event`` on channel _queue_
    # aggregated job states from ``sys.queue`` on channel _queue_
    """
    waiters = {}
    last = []

    def open(self):
        """
        Connects and registers a client in ``.waiters``.
        """
        self.logger.info("connected client %s", self.request.remote_ip)
        EventHandler.waiters[self] = []

    def on_close(self):
        """
        Disconnects and unregisters a client from ``.waiters``.
        """
        self.logger.info("disconnected client %s", self.request.remote_ip)
        del EventHandler.waiters[self]

    def on_message(self, message):
        """
        Processes client messages of ``type``

        * _message_
        * _interest_

        All other or undefined message types are ignored.

        :param message: str representing valid json
        """
        try:
            request = json_decode(message)
        except:
            ret = "error parsing json data"
        else:
            cmd = request.get("type", "unknown")
            if cmd:
                meth = getattr(self, "proc_" + cmd, self.proc_unknown)
                ret = meth(request)
            else:
                ret = "missing message type"
        self.write_message(ret)

    def proc_unknown(self, request):
        """
        Called for all unknown message types.

        :return: dict with ``type`` _error_ and ``message``
        """
        return {
            "type": "error",
            "message": "unknown type"
        }

    def proc_message(self, request):
        """
        Extracts the message ``channel`` and ``text``. If both are defined, an
        event with name ``message`` is created in ``sys.event``. Additionally
        the channel is added to the sending user's interest if not done, yet.

        :param request: dict representing the message with expected message
        ``text`` and ``channel``
        :return: dict with ``type`` _message_ or _error_ and ``message`` text
        """
        channel = request.get("channel", None)
        text = request.get("text", None)
        if channel and text:
            _id = self.trigger(
                name="message",
                channel=channel,
                data=text,
                author=self.current_user
            )
            if EventHandler.waiters[self] is None:
                EventHandler.waiters[self] = []
            interest = EventHandler.waiters[self]
            if channel not in interest:
                EventHandler.waiters[self].append(channel)
                return {
                    "type": "message",
                    "message_id": _id,
                    "message": "OK, added interest in channel"
                }
            return {
                "type": "message",
                "message_id": _id,
                "message": "OK"
            }
        return {
            "type": "error",
            "message_id": None,
            "message": "malformed message"
        }

    def proc_interest(self, request):
        interests = request.get("data", [])
        EventHandler.waiters[self] = list({
            i.lower().strip()
            for i in interests
            if i and isinstance(i, str)})
        self.logger.info("client [%s] requests channel %s",
                         self.request.remote_ip, EventHandler.waiters[self])
        return {
            "type": "interest",
            "data": EventHandler.waiters[self],
            "message": "processed interest in {}".format(
                EventHandler.waiters[self])
        }

    @classmethod
    def on_event(cls, change):
        doc = change["fullDocument"]
        channel = doc.get("channel", None)
        author = doc.get("author", None)
        data = json_encode(doc)
        for waiter, interest in cls.waiters.items():
            if ((channel == core4.const.QUEUE_CHANNEL)
                    or (author != waiter.current_user)):
                if channel in interest:
                    waiter.write_message(data)

    @classmethod
    async def on_queue(cls, change):
        data = {
            "created": core4.util.node.mongo_now(),
            "name": "summary",
            "author": core4.util.node.get_username(),
            "channel": core4.const.QUEUE_CHANNEL,
        }
        for waiter, interest in cls.waiters.items():
            if core4.const.QUEUE_CHANNEL in interest:
                data["data"] = []
                for line in change:
                    qn = line["name"]
                    if not await waiter.user.has_api_access(qn):
                        line["name"] = "UnauthorizedJob"
                    data["data"].append(line)
                if data["data"] != waiter.last:
                    js = json_encode(data)
                    waiter.write_message(js)
                    waiter.last = data["data"]
