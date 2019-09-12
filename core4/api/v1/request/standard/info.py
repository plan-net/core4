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
    """
    Retrieve API endpoint details/help.
    """
    title = "endpoint information"
    author = "mra"

    async def get(self):
        """
        Methods:
            GET /core4/api/v1/_info - list of endpoints

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
            >>> rv = get(url  +  "/_info", cookies=signin.cookies)
            >>> rv.json()
        """
        result = []
        for handler in await self.application.container.get_handler():
            if await self.user.has_api_access(handler["qual_name"]):
                result.append(handler)
        if self.wants_html():
            return self.render(self.info_html_page, data=result)
        self.reply(result)
