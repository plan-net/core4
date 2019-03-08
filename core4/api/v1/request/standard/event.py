from tornado import gen

import core4.const
import core4.util.node
from core4.api.v1.request.websocket import CoreWebSocketHandler
from core4.base.main import CoreBase
from core4.queue.query import QueryMixin
from core4.util.data import json_encode, json_decode

# todo: permission design ... OK
# todo: sticky messages
# todo: queue history endpoint
# todo: maintenance info

QUERY_SLEEP = 1


class EventWatch(CoreBase):

    async def watch(self):
        coll = self.config.sys.event.connect_async()
        async with coll.watch() as change_stream:
            async for change in change_stream:
                EventHandler.on_change(change)


class QueueWatch(CoreBase, QueryMixin):

    async def watch(self):
        coll = self.config.sys.queue.connect_async()
        pipeline = self.pipeline_queue_state()
        while True:
            nxt = gen.sleep(QUERY_SLEEP)
            cursor = coll.aggregate(pipeline)
            data = []
            async for doc in cursor:
                data.append(doc)
            await EventHandler.on_queue(data)
            await nxt


class EventHandler(CoreWebSocketHandler):
    waiters = {}
    last = []

    def open(self):
        self.logger.info("connected client %s", self.request.remote_ip)
        EventHandler.waiters[self] = []

    def on_close(self):
        self.logger.info("disconnected client %s", self.request.remote_ip)
        del EventHandler.waiters[self]

    def on_message(self, message):
        try:
            request = json_decode(message)
        except:
            ret = "error parsing json data"
        else:
            cmd = request.get("type", None)
            meth = getattr(self, cmd, self.unknown)
            ret = meth(request)
        self.write_message(ret)

    def unknown(self, request):
        return {
            "type": "error",
            "message": "unknown type"
        }

    def message(self, request):
        channel = request.get("channel", None)
        message = request.get("message", None)
        if channel and message:
            self.trigger(
                name="message",
                channel=channel,
                data=message,
                author=self.current_user
            )
            if EventHandler.waiters[self] is None:
                EventHandler.waiters[self] = []
            interest = EventHandler.waiters[self]
            if channel not in interest:
                EventHandler.waiters[self].append(channel)
                return {
                    "type": "message",
                    "message": "OK, added interest in channel"
                }
            return {
                "type": "message",
                "message": "OK"
            }
        return {
            "type": "error",
            "message": "malformed message"
        }

    def interest(self, request):
        EventHandler.waiters[self] = list({
            i.lower().strip()
            for i in request.get("data", [])
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
    def on_change(cls, change):
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


"""
>>> from websocket import create_connection
>>> from requests import post, get, put
>>> import json

>>> login = requests.get("http://devops:5001/core4/api/login?username=admin&password=hans")
>>> token = login.json()["data"]["token"]

>>> h = {"Authorization": "Bearer " + token}
>>> rv = post("http://devops:5001/core4/api/v1/roles", headers=h,
>>>           json={
>>>               "name": "test1",
>>>               "realname": "Test User",
>>>               "email": "test1@plan-net.com",
>>>               "password": "hello",
>>>               "perm": ["api://core4.api.v1.request.standard.event.EventHandler",
>>>                        "api://core4.api.v1.request.job.*"]
>>>           })

>>> login2 = requests.get("http://devops:5001/core4/api/login?username=test1&password=hello")
>>> token2 = login2.json()["data"]["token"]

>>> ws = create_connection("ws://devops:5001/core4/api/v1/event?token=" + token2)
>>> ws.send(json.dumps({"type": "interest", "data": ["queue", "message"]}))
>>> while True:
...     print(ws.recv())

>>> rv = get(url + "/roles", headers=h)

>>>             >>> rv = put(url + "/roles/5c824277ad70717c8c366b88", headers=h,
...             >>>           json={
...             >>>               "etag": "5c824516ad70711cb2157ce3",
...             >>>               "perm": ["api://core4.api.v1.request.standard.event.EventHandler", "api://core4.api.v1.request.*", "job://.*/r"]
...             >>>           })
...
"""
