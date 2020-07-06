#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tornado import gen
from tornado.iostream import StreamClosedError

from core4.api.v1.request.main import CoreRequestHandler
from core4.script.chist import build_query
from core4.util.data import json_encode


class LogHandler(CoreRequestHandler):
    """
    Get logging stream.
    """

    author = "mra"
    title = "logging"

    async def get(self):
        """
        See :meth:`.post`.
        """
        # if self.wants_html():
        #     self.render("template/log.html")
        # else:
        await self.post()

    async def post(self):
        """
        Methods:
            POST /log

        Parameters:
            start (str): date, time, datetime or delta with weeks (w), days (d),
                         hours (h) or minutes (h)
            end (str): date, time or datetime
            level (str): minimum level DEBUG, INFO, WARNING, ERROR, CRITICAL
            project (str)
            hostname (str)
            username (str)
            qual_name (str): accepts Python regular expressions
            identifier (str): accepts Python regular expressions
            message (str): accepts Python regular expressions

        Returns:
            - **_id** (ObjectId)
            - **created** (datetime)
            - **epoch** (float)
            - **identifier** (str)
            - **hostname** (str)
            - **username** (str)
            - **levelno** (int)
            - **level** (str)
            - **qual_name** (str)
            - **message** (str)

        Raises:
            401: Unauthorized
            403: Forbidden

        Examples:
            >>> from requests import get
            >>> import json
            >>>
            >>> signin = get("http://0.0.0.0:5001/core4/api/v1/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>>
            >>> rv = get("http://0.0.0.0:5001/core4/api/v1/log?follow=1&start=5m", headers=h, stream=True)
            >>> print(rv.status_code)
            >>>
            >>> part = ""
            >>> for line in rv:
            >>>     part += line.decode("utf-8")
            >>>     if part.endswith("\n\n"):
            >>>         js = json.loads(part.split("\n", 1)[1].split(": ", 1)[1])
            >>>         if "created" in js:
            >>>             print(js["created"], js["message"])
            >>>         part = ""
        """
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_header('X-Accel-Buffering', 'no')
        query = {"$and": self._build_query()}
        follow = self.get_argument("follow", as_type=bool, default=False)
        last_id = None
        while True:
            cur = self.config.sys.log.find(query).sort(
                [("_id", 1)])
            n = 0
            for doc in await cur.to_list(None):
                access = await self.user.has_job_access(doc["qual_name"])
                if not access:
                    access = await self.user.has_api_access(doc["qual_name"])
                if access:
                    if await self.sse("log", doc):
                        break
                last_id = doc["_id"]
                n += 1
            self.logger.debug("query [%d] logs with %s", n, query)
            await gen.sleep(1.)
            if await self.sse("alive", {"request_id": self.identifier}):
                self.finish()
                return
            if not follow:
                break
            if last_id is not None:
                query["_id"] = {"$gt": last_id}
        self.logger.info("closing log stream")
        await self.sse("close", {})
        self.finish()

    def _build_query(self):
        args = {}
        for a in ("start", "end", "level", "project", "hostname", "username",
                  "qual_name", "identifier", "message"):
            args["--" + a] = self.get_argument(a, as_type=str, default=None)
        return build_query(args)

    async def sse(self, event, doc):
        js = json_encode(doc, indent=None, separators=(',', ':'))
        try:
            self.write("event: " + event + "\n")
            self.write("data: " + js + "\n\n")
            await self.flush()
        except StreamClosedError:
            self.logger.info("stream closed")
            return True
        except Exception:
            self.logger.error("stream error", exc_info=True)
            return True
        return False
