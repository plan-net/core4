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


class InfoHandler(CoreRequestHandler):
    title = "server endpoint information"
    author = "mra"

    async def get(self):
        """
        Retrieve API endpoint details/help.

        Methods:
            GET /info/<rsc_id> - endpoint details

        Parameters:
            content_type (str): force json, html, text

        Returns:
            data element with list of dicts, see
            :meth:`.CoreApiContainer.get_handler`

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
        ret = await self.application.container.get_handler()
        if self.wants_html():
            return self.render(self.info_html_page, data=ret)
        self.reply(ret)
