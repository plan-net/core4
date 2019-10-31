#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import random
import string

from core4.api.v1.request.role.access.handler.mongo import MongoHandler
from core4.api.v1.request.role.access.handler.postgres import PostgresHandler
import core4.base
import core4.error

#: password length used to create MongoDB access
PASSWORD_LENGTH = 32
#: key/value pairs of permission protocols and access handlers
HANDLER = {
    "mongodb": MongoHandler,
    "postgres": PostgresHandler
}


class CoreAccessManager(core4.base.CoreBase):
    """
    The :class:`.CoreAccessManager` processes all permissions defined for a
    core4 role. The :meth:`synchronise` method executes the following workflow
    for all protocols with the appropriate access handler as defined in module
    variable :attr:`HANDLER`:

    #. delete role if it exists (handler method ``.del_role()``)
    #. create the role (handler method ``.add_role()``)
    #. create access token (password to be used together with the role`s name)
    #. grant read permissions for each permission with the appropriate protocol
       (handler method ``.grant(db)``)
    #. call the handler's ``.finish()`` method

    Currently only the handler :class:`.MongoHandler` is defined to grant
    read-only permissions to MongoDB databases (e.g. ``mongodb://dbname``) and
    read/write access permissions to the role's custom collection in MongoDB
    database `user` (e.g. MongoDB collection ``user.<USERNAME>``).
    """

    def __init__(self, role, *args, **kwargs):
        """
        Initialises access management for the passed core4 role/user.

        :param role: :class:`.core4.api.v1.role.Role`
        """
        super().__init__(*args, **kwargs)
        self.token = None
        if not role.is_user:
            raise core4.error.Core4UsageError(
                "cannot synchronise core4 roles, only users")
        self.role = role

    def create_token(self):
        """
        This method creates a random password of length :attr:`PASSWORD_LENGTH`
        for the user to access the database

        :return: token/password (str)
        """
        if self.token is None:
            token = ''.join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits) for _
                in range(PASSWORD_LENGTH))
            self.token = token
        return self.token

    async def synchronise(self, protocol):
        """
        Executes the access management workflow for the passed handler as
        defined by the role's access permission (see :class:`.PermField` and
        :class:`.Role`.

        :return: access token (password)
        """
        handler = HANDLER[protocol](self.role, self.create_token())
        await handler.del_role()
        token = await handler.add_role()
        perms = await self.role.casc_perm()
        for perm in perms:
            (proto, *database) = perm.split("://")
            if proto == protocol:
                dbname = "://".join(database)
                await handler.grant(dbname)
        await handler.finish()
        return token

    async def synchronise_all(self):
        access = {}
        for proto in HANDLER:
            access[proto] = await self.synchronise(proto)
        return access

    async def reset(self, protocol):
        handler = HANDLER[protocol](self.role, self.token)
        await handler.del_role()

    async def reset_all(self):
        for proto in HANDLER:
            await self.reset(proto)
