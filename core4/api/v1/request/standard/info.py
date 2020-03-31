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
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/_info")
            >>> rv.json()
        """
        if self.request.query.lower() == "version":
            return await self.post()
        result = []
        for handler in await self.application.container.get_handler():
            check = []

            # self.logger.info("handler: [%s]", str(handler))

            if handler["perm_base"] == "handler":
                check.append(handler["qual_name"])
            elif handler["perm_base"] == "container":
                check += handler["container"]
            for test in check:
                if await self.user.has_api_access(test):
                    result.append(handler)
                    break
        if self.wants_html():
            return self.render(self.info_html_page, data=result)
        self.reply(result)

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
