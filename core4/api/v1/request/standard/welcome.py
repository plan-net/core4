#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements core4os welcome widget.
"""

from core4.api.v1.request.main import CoreRequestHandler
import core4
from core4.api.v1.request.store import CoreStore
from core4.queue.query import QueryMixin


class WelcomeHandler(CoreRequestHandler):
    """
    Release Notes
    """
    author = "mra"
    title = "core4os 4.1"
    subtitle = "Welcome Message"
    tag = ["settings"]
    icon = "mdi-star"

    async def get(self):
        """
        Methods:
            GET /core4/api/v1/welcome

        Parameters:
            None

        Returns:
            static HTML page with latest release notes from
            ``./template/welcome.html``

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/welcome")
            >>> rv
        """
        self.render("template/welcome.html", version=core4.__version__)
