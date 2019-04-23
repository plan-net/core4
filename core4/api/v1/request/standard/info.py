#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.InfoHandler` to retrieve API endpoint details.
"""

from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.query import QueryMixin


class InfoHandler(CoreRequestHandler, QueryMixin):
    title = "server endpoint information"
    author = "mra"

    async def get(self):
        """
        Retrieve API endpoint details/help.

        Methods:
            GET /info/<route_id> - endpoint details

        Parameters:
            content_type (str): force json, html, text

        Returns:
            data element with dict of

            - **project** (*str*): title
            - **args** (*dict*): passed from the :class:`.CoreApiContainer` to
              the handler
            - **qual_name** (*str*): of the endpoint
            - **author** (*str*): of the request handler
            - **description** (*str*): method doc string in HTML format
            - **icon** (*str*): material icon
            - **title** (*list*): of the endpoint
            - **pattern** (*list*): of *str* with URL matching pattern
            - **route_id** (*str*): MD5 of the route/pattern
            - **tag** (*list*): of tag strings
            - **container** (*class*): name serving the endpoint
            - **protected** (*bool*): if the request handler is protected
            - **version** (*str*): of the project
            - **error** (*list*): of parsing error messages from
              :mod:`docutils`
            - **card_url** (*str*): URL to card page
            - **enter_url** (*str*): URL to enter
            - **help_url** (*str*): URL to help page
              :meth:`.reverse_url`
            - **method** (*list*): with method details

              - **method** (str): ``GET``, ``POST``, ``DELETE``, etc.
              - **doc** (str): plain RST method doc string
              - **html** (str): method doc string in HTML format
              - **parts** (dict): of bool if the sections *method*, *example*,
                *parameter*, *raise*, are defined
              - **extra_parts** (list): of additional sections
              - **parser_error** (list): of parsing erreors

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get, post, delete, put
            >>> from pprint import pprint
            >>> import random
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get("http://localhost:5001/core4/api/info/8ff1580edf27b12d4231567be936a0d6",
            cookies=signin.cookies)
            >>> rv.json()
        """
        ret = await self.get_handler()
        if self.wants_html():
            return self.render("template/widget.html",
                               data=ret)
        self.reply(ret)

    async def get_card(self, rsc_id):
        handler = self.application.lookup[rsc_id]["handler"]
        return handler.__doc__

    async def get_handler(self):
        alive = [(d["protocol"], d["hostname"], d["port"])
                 for d in await self.get_daemon_async(kind="app")]
        handler = {}
        inactive = 0
        async for doc in self.config.sys.handler.find():
            if ((doc["protocol"], doc["hostname"], doc["port"]) in alive) \
                    and (doc["started_at"] is not None):
                del doc["_id"]
                handler.setdefault(doc["rsc_id"], []).append(doc)
            else:
                inactive += 1
        self.logger.debug("found [%d] handler alive, [%d] inactive",
                          len(handler), inactive)
        ret = []
        detail = ("hostname", "protocol", "port", "routing", "container")
        for rsc_id, data in handler.items():
            first = data[0].copy()
            for attr in detail:
                del first[attr]
            first["endpoint"] = []
            info = set()
            for d in data:
                for c in d["container"]:
                    url = "{}{}".format(
                        d["routing"], c[2])
                    info.add(url)
                for k in ("started_at", "created_at"):
                    first[k] = min(first[k], d[k])
            first["endpoint"] += sorted(list(info))
            ret.append(first)
        ret.sort(key=lambda r: (str(r["title"]), r["qual_name"]))
        return ret
