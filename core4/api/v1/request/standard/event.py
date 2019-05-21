#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tornado import gen

import core4.const
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.websocket import CoreWebSocketHandler
from core4.base.main import CoreBase
from core4.queue.query import QueryMixin
from core4.util.data import json_encode, json_decode
from core4.util.pager import CorePager


# todo: sticky messages

class EventWatch(CoreBase):
    """
    Watches collection ``sys.event`` for any changes using MongoDB _watch_
    feature. All changes are forwarded to :class:`.EventHandler` using
    :meth:`on_event <.EventHandler.on_event>` method.
    """
    change_stream = None

    async def watch(self):
        coll = self.config.sys.event.connect_async()
        async with coll.watch() as EventWatch.change_stream:
            async for change in EventWatch.change_stream:
                if change:
                    EventHandler.on_event(change)


class QueueWatch(CoreBase, QueryMixin):
    """
    Continuously queries ``sys.queue`` and forwards to :class:`.EventHandler`
    using :meth:`on_queue <.EventHandler.on_queue>` method.
    """

    stop = False

    async def watch(self):
        QueueWatch.stop = False
        coll = self.config.sys.queue.connect_async()
        pipeline = self.pipeline_queue_state()
        interval = self.config.event.queue_interval
        while not QueueWatch.stop:
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

    #. chat messages on channel _message_
    #. job events from ``sys.event`` on channel _queue_
    #. aggregated job states from ``sys.queue`` on channel _queue_

    See :doc:`/example/index` for an example about _events_ and an example
    about _messages_.
    """
    author = "mra"
    title = "event web socket"
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
            meth = getattr(self, "proc_" + cmd, self.proc_unknown)
            ret = meth(request)
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
                name=core4.const.MESSAGE_CHANNEL,
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
                    "type": "interest",
                    "message_id": _id,
                    "message": "OK, added interest in channel"
                }
            return {
                "type": "send",
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
        channel = 'event'
        author = doc.get("author", None)
        doc['channel'] = 'event'
        data = json_encode(doc)
        for waiter, interest in cls.waiters.items():
            if ((channel == core4.const.EVENT_CHANNEL)
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


class EventHistoryHandler(CoreRequestHandler):
    """
    """
    author = "mra"
    title = "event history handler"

    # todo: write documentation
    async def get(self):
        """
        Methods:
            GET /event/history

        Parameters:
            per_page (int): number of events per page
            page (int): requested page (starts counting with ``0``)
            filter (dict): optional mongodb filter

        Returns:
            data element with list of events with

            - **channel** (str): channel, defaults to ``message``
            - **author** (str): sender (role name)
            - **created** (datetime): when the message was sent
            - **data** (str): message text

            For pagination the following top level attributes are returned:

            - **total_count** (int): the total number of records
            - **count** (int): the number of records in current page
            - **page** (int): current page (starts counting with ``0``)
            - **page_count** (int): the total number of pages
            - **per_page** (int): the number of elements per page

        Raises:
            401: Unauthorized
            403: Forbidden

        Examples:
            >>> from requests import post, get, put
            >>>
            >>> login = get("http://devops:5001/core4/api/login?username=admin&password=hans")
            >>> token = login.json()["data"]["token"]
            >>> rv = post("http://devops:5001/core4/api/v1/roles",
            ...           headers={"Authorization": "Bearer " + token},
            ...           json={
            ...               "name": "test",
            ...               "realname": "Test User",
            ...               "email": "test@plan-net.com",
            ...               "password": "very secret",
            ...               "role": ["standard_user"],
            ...               "perm": ["api://core4.api.v1.request.queue.history.*"]
            ...           })
            >>> rv
            <Response [200]>
            >>> user_login = get("http://devops:5001/core4/api/login?username=test&password=very secret")
            >>> user_token = user_login.json()["data"]["token"]
            >>>
            >>> from websocket import create_connection
            >>> import json
            >>>
            >>> ws = create_connection("ws://devops:5001/core4/api/v1/event?token=" + user_token)
            >>> ws.send(json.dumps({"type": "interest", "data": ["message"]}))
            >>> ws.recv()
            '{"message": "processed interest in [\'message\']", "data": ["message"], "type": "interest"}'
            >>> for i in range(0, 100):
            ...     ws.send(json.dumps({"type": "message", "channel": "message", "text": "hello, this is message no. %d" %(i+1)}))
            >>>
            >>> rv = get("http://devops:5001/core4/api/v1/event/history?page=1&per_page=5&token=" + user_token)
            >>> rv.json()
            {'_id': '5c8560b4ad7071213033a3d7',
             'code': 200,
             'count': 5,
             'data': [{'_id': '5c855f3cad70712130873f60',
               'author': 'test',
               'channel': 'message',
               'created': '2019-03-10T19:02:20',
               'data': 'hello, this is message no. 95'},
              {'_id': '5c855f3cad70712130873f5f',
               'author': 'test',
               'channel': 'message',
               'created': '2019-03-10T19:02:20',
               'data': 'hello, this is message no. 94'},
              {'_id': '5c855f3cad70712130873f5e',
               'author': 'test',
               'channel': 'message',
               'created': '2019-03-10T19:02:20',
               'data': 'hello, this is message no. 93'},
              {'_id': '5c855f3cad70712130873f5d',
               'author': 'test',
               'channel': 'message',
               'created': '2019-03-10T19:02:20',
               'data': 'hello, this is message no. 92'},
              {'_id': '5c855f3cad70712130873f5c',
               'author': 'test',
               'channel': 'message',
               'created': '2019-03-10T19:02:20',
               'data': 'hello, this is message no. 91'}],
             'message': 'OK',
             'page': 1,
             'page_count': 21,
             'per_page': 5,
             'timestamp': '2019-03-10T19:08:36.187955',
             'total_count': 101.0}
        """

        per_page = self.get_argument("per_page", as_type=int, default=10)
        current_page = self.get_argument("page", as_type=int, default=0)
        query_filter = self.get_argument("filter", as_type=dict, default={})
        coll = self.config.sys.event
        query = {
            "channel": core4.const.MESSAGE_CHANNEL
        }
        if query_filter:
            query.update(query_filter)

        async def _length(filter):
            return await coll.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            cur = coll.find(
                filter,
                projection={"created": 1, "data": 1, "_id": 1, "author": 1,
                            "channel": 1}
            ).sort(
                [("$natural", -1)]
            ).skip(
                skip
            ).limit(
                limit
            )
            ret = []
            for doc in await cur.to_list(length=limit):
                ret.append(doc)
            return ret

        pager = CorePager(per_page=per_page,
                          current_page=current_page,
                          length=_length, query=_query,
                          filter=query)
        page = await pager.page()
        return self.reply(page)

    async def post(self):
        """
        Same as :meth:`get`.
        """
        return self.get()
