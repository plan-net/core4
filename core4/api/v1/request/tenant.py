#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 :class:`.CoreTenantHandler`, based on :class:`.CoreRequestHandler`. This
class supports multi-client access control.
"""

from core4.api.v1.request.main import CoreRequestHandler


class CoreTenantHandler(CoreRequestHandler):
    """
    Supports multi-client access control management. The handler first verifies,
    if the user is a cop. If not, the handler verifies the user has access to
    the request handler as specified by the permission scheme ``api://``. If
    yes, the handler finally verifies the user has access to the client as
    specified by the permission scheme ``app://client/[client-name]``. The
    client is extracted from the request URL path. The client pattern needs to
    be specified in the handler's route pattern, e.g.::

        # the client is the first group of the pattern

        /root/request/(.+)/(.*)

        # the client is represented by the pattern group "tenant"
        #   with named pattern groups, all patterns must have a name

        /root/request/(?P<tenant>.+)/(?P<id>.*) #
    """
    async def verify_access(self):
        """
        Verifies the user has access to the handler using
        :meth:`User.has_api_access` and to the client using
        :meth:`.has_client_access`.

        :return: ``True`` for success, else ``False``
        """
        if self.user and await self.user.has_api_access(self.qual_name()):
            if "client" in self.path_kwargs:
                client = self.path_kwargs.get("client")
                del self.path_kwargs["client"]
            else:
                client = self.path_args.pop(0)
            self.client = client
            return await self.user.has_client_access(client)
        return False

    # async def has_client_access(self, client):
    #     """
    #     Verifies the user has a valid permission ``app://client/[client-name]``.
    #
    #     :param client: client (str) extracted from the URL
    #     :return: ``True`` for success, else ``False``
    #     """
    #     return self.user.has_client_access(client)
