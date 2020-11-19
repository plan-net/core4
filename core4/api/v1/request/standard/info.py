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
from core4.util.pager import CorePager
import pql
import re

class InfoHandler(CoreRequestHandler):
    """
    API endpoint details, help and tag summary.
    """
    title = "endpoint information"
    author = "mra"

    async def get(self):
        """
        Methods:
            GET /core4/api/v1/_info - paginated list of endpoints

        Parameters:
            per_page (int)
            current_page (int)
            query (dict)
            serach (str)

        The search attributes support

        #. free text search, for example ``foobar``
        #. a domain specific query language filtering the following attributes,
           for example ``tag == "app" or tag == "role" or title == regex("role.*", "i")``
        #. hiding/showing technical APIs flagged with the *api* tag by prefixing
           the search string with a "!" character, for example ``! foobar``
           (free text search on all APIs including the technical APIs) or
           ``! tag == "app" or tag == "role" or title == regex("role.*", "i")``.

        See https://github.com/alonho/pql for a complete description of the
        domain specific query language.

        Returns:
            data element with list of dicts, see
            :meth:`.CoreApiContainer.get_handler`

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/_info")
            >>> rv.json()

        Methods:
            GET /core4/api/v1/_info?version - project and repository version

        Parameters:
            None

        Returns:
            data element with version string of the project and version string
            of installed core4.

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/_info?version"
                         "?page=1&search=!foobar")
            >>> rv.json()

        Methods:
            GET /core4/api/v1/_info?tag- list of use API endpoint tags

        Parameters:
            None

        Returns:
            data element with list of dicts including the attribute ``default``
            (bool) to indicate default versus custom tags.

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/_info?tag")
            >>> rv.json()
        """
        if self.request.query.lower() == "version":
            return await self.post()
        elif self.request.query.lower() == "tag":
            return await self.list_tag()
        elif self.request.query.lower() == "widget":
            return await self.list_widget()
        return await self.list_widget()

    async def post(self):
        """
        Retrieve project name, version and core4 version. This data can be
        retrieved with ``GET /core4/api/v1/_info?version``, too.

        Methods:
            POST /core4/api/v1/_info - project and core4 version

        Parameters:
            none

        Returns:
            data element with dict of version, project and core4 version

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import post
            >>> rv = post("http://localhost:5001/core4/api/v1/_info")
            >>> rv.json()
        """
        self.reply(
            {
                "project": self.application.container.project,
                "version": self.application.container.version(),
                "core4": self.version()
            }
        )

    async def list_tag(self):
        tag = {}
        for handler in await self.application.container.get_handler():
            check = []
            if handler["perm_base"] == "handler":
                check.append(handler["qual_name"])
            elif handler["perm_base"] == "container":
                check += handler["container"]
            for test in check:
                if await self.user.has_api_access(test, info_request=True):
                    for t in handler["tag"]:
                        tag.setdefault(t, {"count": 0, "default": False})
                        tag[t]["count"] += 1
                    break
        for t in self.config.api.tag:
            tag.setdefault(t, {"count": 0, "default": False})
            tag[t]["default"] = True
        self.reply(tag)

    async def list_widget(self):
        # parse arguments
        per_page = int(self.get_argument("per_page", as_type=int, default=10))
        current_page = int(self.get_argument("page", as_type=int, default=0))
        query = self.get_argument("filter", as_type=dict, default={})
        search = self.get_argument("search", as_type=str, default=None)
        all = False
        # parse search
        if search:
            search = search.strip()
            if search.startswith("!"):
                search = search[1:].lstrip()
                all = True
            if search:
                try:
                    q = pql.find(search)
                    self.logger.debug("search: %s", q)
                except:
                    search = ".*" + search + ".*"
                    q = {"$or": [
                        {"author": re.compile(search, re.I)},
                        {"description": re.compile(search, re.I)},
                        {"qual_name": re.compile(search, re.I)},
                        {"subtitle": re.compile(search, re.I)},
                        {"tag": re.compile(search, re.I)},
                        {"title": re.compile(search, re.I)}
                    ]}
                query.update(q)
        # search
        if not all:
            query = {"$and": [query, {"tag": {"$ne": "api"}}]}
        data = []
        for handler in await self.application.container.get_handler(**query):
            check = []
            if handler["perm_base"] == "handler":
                check.append(handler["qual_name"])
            elif handler["perm_base"] == "container":
                check += handler["container"]
            for test in check:
                if await self.user.has_api_access(test, info_request=True):
                    data.append(handler)
                    break

        data.sort(key=lambda d: (
            (d["title"] or "").lower(), (d["subtitle"] or "").lower()))

        # paginate
        async def _length(*_, **__):
            return len(data)

        async def _query(skip, limit, *_, **__):
            return data[skip:(skip + limit)]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query,
                          sort_by=None,
                          filter=None)
        ret = await pager.page()
        return self.reply(ret)
