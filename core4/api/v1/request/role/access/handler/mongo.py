#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import random
import string

from core4.api.v1.request.role.access.handler import BaseHandler

#: password length used to create MongoDB access
PASSWORD_LENGTH = 32


class MongoHandler(BaseHandler):
    """
    This class handles MongoDB access permissions. The handler is registered
    in :attr:core4.service.access.manager.HANDLER` attribute.

    The handler provides read-only access to MongoDB databases specified by
    the user/role permission field (``mongodb://<DBNAME>``). Additionally the
    handler creates user database at ``user!<USERNAME>`` with the built-in
    ``dbOwner`` role assigned to the user.

    .. note:: The prefix of the user database (``user!``) can be defined with
              core4 configuration option ``sys.userdb``.
    """

    def __init__(self, role, *args, **kwargs):
        super().__init__(role, *args, **kwargs)
        self.token = None
        coll = self.config.sys.admin.connect_async()
        self.admin_db = coll.connection[self.config.sys.admin.database]

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

    async def revoke_access(self):
        """
        This method deletes the MongoDB user and role if exist.
        :return:
        """
        username = self.role.name
        user_info = await self.admin_db.command("usersInfo", username)
        if user_info["users"]:
            await self.admin_db.command('dropUser', username)
            self.logger.info('removed mongo user [%s]', username)
        else:
            self.logger.debug("mongo user [%s] not found", username)


    async def revoke(self):
        """
        This method deletes the Roles of MongoDB.
        """
        username = self.role.name
        user_info = await self.admin_db.command("usersInfo", username)
        if user_info["users"]:
            self.logger.info('revokes Roles from user [%s]', username)
            # results for every matched user
            for u in user_info['users']:
                # check if roles exists and ddddeeelete only read premissions
                to_delete = [d for d in u.get('roles') if d['role'] != 'dbOwner']
                if to_delete:
                    self.logger.info('revokes Roles [%s] from user [%s]', u.get('roles'), username)
                    await self.admin_db.command('revokeRolesFromUser', username, roles=to_delete)
        else:
            self.logger.debug("mongo user [%s] not found", username)

    async def grant_access(self):
        """
        This method creates the role and returns the token/password created by
        :meth:`.create_token`.

        .. note:: The user is created in MongoDB admin system database,
                  collection ``system.users``. Additionally the MongoDB
                  built-in role *dbOwner* is granted on database
                  ``user!<USERNAME>``. The prefix *user!* can be configured
                  with core4 configuration option ``sys.userdb``.

        :return: token/password (str)
        """
        # create the role
        username = self.role.name
        password = self.create_token()
        userdb = "".join([self.config.sys.userdb, username])
        # check if user exists
        user_info = await self.admin_db.command("usersInfo", username)
        if user_info["users"]:
            await self.admin_db.command('updateUser', username, pwd=password,
                                  roles=[])
        else:
           await self.admin_db.command('createUser', username, pwd=password,
                                    roles=[])
        await self.admin_db.command(
            'grantRolesToUser', username,
            roles=[{'role': 'dbOwner', 'db': userdb}])
        self.logger.info(
            'created mongo user [%s] with private [%s]', username, userdb)
        return password

    async def grant(self, database):
        """
        cascade database permissions and read-only access.

        :param database: to grant
        """
        username = self.role.name
        await self.admin_db.command(
            'grantRolesToUser', username,
            roles=[{'role': 'read', 'db': database}])
        self.logger.info('grant role [%s] access to [%s]', username, database)

