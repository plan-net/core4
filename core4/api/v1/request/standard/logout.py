#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements core4 standard :class:`LogoutHandler`.
"""

from core4.api.v1.request.standard.login import LoginHandler


class LogoutHandler(LoginHandler):
    """
    core4os standard Logout Handler.
    """
    title = "Logout Handler"
    author = "mra"
    protected = True

    async def get(self):
        """
        Logout an authenticated user.

        This request resets the secure cookie. Further actions have
        to be taken by the client itself, e.g. resetting the token
        or resetting client basic authentication. The latter
        typically requires to restart the client.

        Methods:
            POST /core4/api/v1/logout

        Parameters:
            None

        Returns:
            data element with ``OK``

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>> url = "http://localhost:5001/core4/api/login"
            >>> signin = get(url + "?username=admin&password=hans")
            >>> h = {"Authorization": "Bearer " + signin.json()["data"]["token"]}
            >>> signin.status_code
            200
            >>> rv = get("http://localhost:5001/core4/api/logout", headers=h)
            >>> rv
            {
                '_id': '5bd9b796de8b692fd5f5f768',
                'code': 200,
                'data': 'OK',
                'message': 'OK',
                'timestamp': '2018-10-31T14:09:26.114443'
            }
        """
        self.clear_all_cookies()
        await self.getter(True)
        self.current_user = None

    async def post(self):
        """
        Same as :meth:`.post`
        """
        await self.get()
