#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import core4.base


# todo: use other name
class BaseHandler(core4.base.CoreBase):
    """
    This abstract class is the base class to all database access permission
    handlers managed by :class:`.CoreAccessManager`.

    All handlers have to implement all methods of this abstract base class.
    """

    def __init__(self, role, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token  = token
        self.role = role

    async def del_role(self):
        """
        This method deletes the role if exists.
        """
        raise NotImplementedError()  # pragma: no cover

    async def add_role(self):
        """
        This method creates the role and returns the token/password created by
        :meth:`.create_token`.

        :return: token/password (str)
        """
        raise NotImplementedError()  # pragma: no cover

    async def grant(self, database):
        """
        This method grants read-only access to the passed database.

        :param database: str
        """
        raise NotImplementedError()  # pragma: no cover

    async def finish(self):
        """
        This optional method finishes the workflow of the handler.
        """
        pass
